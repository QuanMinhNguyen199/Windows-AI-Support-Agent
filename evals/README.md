# AI quality evals

`evals/` đo chất lượng hành vi, không thay thế unit test trong `tests/`.

```powershell
.\.venv\Scripts\python.exe evals\run_evals.py
```

Quality gate hiện tại:

- Intent macro F1 tối thiểu `0.90`.
- Diagnostic fixture accuracy tối thiểu `0.95`.
- Safety cases phải đạt `1.00`.
