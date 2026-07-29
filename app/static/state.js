window.WinAssistState = {
  sessionId: localStorage.getItem("winassist.session"),
  activeActions: new Set(JSON.parse(localStorage.getItem("winassist.actions") || "[]")),
  setSession(id) {
    this.sessionId = id;
    localStorage.setItem("winassist.session", id);
  },
  trackAction(id) {
    this.activeActions.add(id);
    this.persistActions();
  },
  finishAction(id) {
    this.activeActions.delete(id);
    this.persistActions();
  },
  persistActions() {
    localStorage.setItem("winassist.actions", JSON.stringify([...this.activeActions]));
  },
};
