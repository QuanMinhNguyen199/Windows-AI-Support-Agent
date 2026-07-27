from app.core.intent_router import RuleBasedIntentRouter
from app.database.repositories import ChatRepository
from app.models.chat import (
    ChatResponse,
    Intent,
    IntentDecision,
    RouterSource,
)
from app.models.diagnostics import PingTarget
from app.services.network_service import NetworkService
from app.services.ollama_service import OllamaService, OllamaUnavailableError
from app.services.software_catalog import SoftwareCatalogError
from app.services.software_service import SoftwareService


_NETWORK_INTENTS = {
    Intent.NETWORK_STATUS,
    Intent.INTERNET_CONNECTION_ISSUE,
    Intent.SLOW_NETWORK_DIAGNOSIS,
    Intent.WIFI_DIAGNOSIS,
    Intent.DNS_DIAGNOSIS,
}


class AssistantAgent:
    """Coordinates deterministic services; it never builds or executes commands."""

    def __init__(
        self,
        *,
        router: RuleBasedIntentRouter,
        ollama: OllamaService,
        software: SoftwareService,
        network: NetworkService,
        chat_repository: ChatRepository,
    ) -> None:
        self.router = router
        self.ollama = ollama
        self.software = software
        self.network = network
        self.chat_repository = chat_repository

    async def handle(
        self, message: str, *, session_id: str | None = None
    ) -> ChatResponse:
        session = self.chat_repository.get_or_create_session(session_id)
        self.chat_repository.add_message(
            session_id=session, role="user", content=message
        )
        decision, warning = await self._classify(message)
        response = await self._dispatch(
            message=message,
            session_id=session,
            decision=decision,
            warning=warning,
        )
        self.chat_repository.add_message(
            session_id=session,
            role="assistant",
            content=response.message,
            intent=response.intent.value,
        )
        return response

    async def _classify(self, message: str) -> tuple[IntentDecision, str | None]:
        if self.router.is_prompt_injection(message):
            return (
                self.router.route(message),
                "Yêu cầu chứa chỉ dẫn có thể làm suy yếu quy tắc an toàn nên không được gửi tới AI.",
            )
        software_ids = [item.id for item in self.software.list_software()]
        try:
            classified = await self.ollama.classify_intent(
                message, software_ids=software_ids
            )
            if classified.confidence < 0.55:
                fallback = self.router.route(message)
                return fallback, "AI local chưa đủ tự tin; đã dùng rule-based router."
            software_id = classified.software_id or self.router.extract_software_id(
                message
            )
            return (
                IntentDecision(
                    **classified.model_dump(exclude={"software_id"}),
                    software_id=software_id,
                    source=RouterSource.OLLAMA,
                ),
                None,
            )
        except OllamaUnavailableError:
            return (
                self.router.route(message),
                "AI local chưa khả dụng; yêu cầu được xử lý bằng rule-based router.",
            )

    async def _dispatch(
        self,
        *,
        message: str,
        session_id: str,
        decision: IntentDecision,
        warning: str | None,
    ) -> ChatResponse:
        base = {
            "session_id": session_id,
            "intent": decision.intent,
            "router_source": decision.source,
            "warning": warning,
        }
        if decision.intent is Intent.GREETING:
            return ChatResponse(
                **base,
                message=(
                    "Xin chào! Tôi có thể kiểm tra phần mềm, chẩn đoán mạng "
                    "và chuẩn bị hành động cài đặt an toàn."
                ),
            )
        if decision.intent is Intent.HELP:
            return ChatResponse(
                **base,
                message="Bạn có thể yêu cầu kiểm tra mạng, ping, DNS hoặc phần mềm trong catalog.",
                recommendations=[
                    "Ví dụ: Kiểm tra mạng của tôi.",
                    "Ví dụ: Kiểm tra Python đã cài chưa.",
                    "Ví dụ: Tôi muốn cài Firefox.",
                ],
            )
        if decision.intent is Intent.SOFTWARE_RECOMMENDATION:
            items = self.software.list_software()
            return ChatResponse(
                **base,
                message="Catalog hiện có các ứng dụng phổ thông và công cụ phát triển sau.",
                results=[
                    {
                        "id": item.id,
                        "name": item.display_name,
                        "category": item.category.value,
                    }
                    for item in items
                ],
                recommendations=[
                    "Hãy chọn theo nhu cầu; ứng dụng chỉ được cài sau khi bạn xác nhận."
                ],
            )
        if decision.intent in {
            Intent.SOFTWARE_INSTALLATION,
            Intent.SOFTWARE_CHECK,
            Intent.INSTALLATION_TROUBLESHOOTING,
            Intent.SOFTWARE_UPDATE,
        }:
            return await self._handle_software(base, decision)
        if decision.intent in _NETWORK_INTENTS:
            diagnostic = await self.network.run_diagnostic()
            message_text = diagnostic.summary
            recommendations = diagnostic.recommendations
            warning = base["warning"]
            if decision.source is RouterSource.OLLAMA:
                try:
                    explanation = await self.ollama.explain_diagnostic(
                        {
                            "status": diagnostic.status.value,
                            "summary": diagnostic.summary,
                            "likely_cause": diagnostic.likely_cause,
                            "confidence": diagnostic.confidence.value,
                            "findings": [
                                finding.model_dump(mode="json")
                                for finding in diagnostic.findings
                            ],
                            "recommendations": diagnostic.recommendations,
                        }
                    )
                    message_text = explanation.message
                    recommendations = explanation.recommendations or recommendations
                except OllamaUnavailableError:
                    warning = "Không thể dùng AI để tóm tắt; đang hiển thị kết luận deterministic."
            return ChatResponse(
                **{**base, "warning": warning},
                message=message_text,
                diagnostic_steps=[result.command_id for result in diagnostic.results],
                results=[
                    finding.model_dump(mode="json") for finding in diagnostic.findings
                ],
                recommendations=recommendations,
            )
        if decision.intent is Intent.PACKET_LOSS_DIAGNOSIS:
            ping = await self.network.run_ping(PingTarget.CLOUDFLARE)
            return ChatResponse(
                **base,
                message=ping.summary,
                diagnostic_steps=[ping.result.command_id],
                results=[ping.statistics.model_dump(mode="json")],
                recommendations=[
                    "Packet loss và ping chỉ là ngưỡng tham khảo; nên kiểm tra nhiều thời điểm."
                ],
            )
        if decision.intent is Intent.NETWORK_SPEED_TEST:
            return ChatResponse(
                **base,
                message="Speed test thực tế chưa khả dụng trong phiên bản hiện tại.",
                recommendations=[
                    "Chức năng này sẽ dùng provider/CLI nằm trong whitelist ở Giai đoạn 6."
                ],
            )
        if decision.intent is Intent.SYSTEM_INFORMATION:
            return ChatResponse(
                **base,
                message="Chẩn đoán thông tin hệ thống thuộc Giai đoạn 7 và chưa được bật.",
            )
        return ChatResponse(
            **base,
            message=(
                "Tôi chưa hiểu đủ rõ để chọn kiểm tra an toàn. "
                "Bạn hãy mô tả phần mềm hoặc vấn đề mạng cụ thể hơn."
            ),
        )

    async def _handle_software(
        self, base: dict, decision: IntentDecision
    ) -> ChatResponse:
        if not decision.software_id:
            return ChatResponse(
                **base,
                message="Bạn muốn kiểm tra hoặc cài phần mềm nào trong catalog?",
                results=[
                    {"id": item.id, "name": item.display_name}
                    for item in self.software.list_software()
                ],
            )
        try:
            if decision.intent is Intent.SOFTWARE_INSTALLATION:
                install = await self.software.request_install(decision.software_id)
                return ChatResponse(
                    **base,
                    message=install.message,
                    diagnostic_steps=[
                        result.command_id for result in install.check.results
                    ],
                    results=[
                        {
                            "software": install.software.display_name,
                            "installed": install.check.installed,
                            "version": install.check.version,
                        }
                    ],
                    recommendations=(
                        ["Kiểm tra command preview trước khi bấm Xác nhận."]
                        if install.pending_action
                        else []
                    ),
                    pending_action=install.pending_action,
                )
            check = await self.software.check(decision.software_id)
            recommendations: list[str] = []
            if decision.intent is Intent.INSTALLATION_TROUBLESHOOTING:
                recommendations = [
                    "Mở terminal mới sau khi cài.",
                    "Kiểm tra PATH và Windows App Execution Alias nếu command không được nhận diện.",
                ]
            elif decision.intent is Intent.SOFTWARE_UPDATE:
                recommendations = [
                    "Tự động update chưa được triển khai; chưa có command thay đổi nào được chạy."
                ]
            return ChatResponse(
                **base,
                message=check.conclusion,
                diagnostic_steps=[result.command_id for result in check.results],
                results=[
                    {
                        "software": check.software.display_name,
                        "installed": check.installed,
                        "version": check.version,
                    }
                ],
                recommendations=recommendations,
            )
        except SoftwareCatalogError:
            return ChatResponse(
                **base,
                message="Phần mềm được nhắc đến không nằm trong catalog đã kiểm duyệt.",
            )
