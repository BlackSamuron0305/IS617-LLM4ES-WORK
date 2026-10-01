"""Local Hugging Face transformers back-end (slow fallback; vLLM is preferred).

Imports ``transformers`` and ``torch`` lazily. Not thread-safe: use workers: 1.
"""

from __future__ import annotations

import time

from ..config import ModelSpec
from .base import ChatRequest, ChatResponse, NonRetryableProviderError, Provider, ProviderConfigError


class HFLocalProvider(Provider):
    name = "hf_local"

    def __init__(self, spec: ModelSpec):
        super().__init__(spec)
        self._tok = None
        self._model = None
        self._torch = None

    def check_ready(self) -> None:
        try:
            import torch  # noqa: PLC0415
            from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415
        except ImportError as e:
            raise ProviderConfigError("hf_local needs `pip install -e .[local]` plus a PyTorch build") from e
        self._torch = torch
        self._tok = AutoTokenizer.from_pretrained(self.spec.model_id)
        self._model = AutoModelForCausalLM.from_pretrained(self.spec.model_id, torch_dtype="auto",
                                                           device_map="auto")

    def complete(self, request: ChatRequest) -> ChatResponse:
        if self._model is None:
            self.check_ready()
        torch = self._torch
        kwargs = dict((self.spec.extra_body or {}).get("chat_template_kwargs", {}))
        try:
            inputs = self._tok.apply_chat_template(request.messages, add_generation_prompt=True,
                                                   return_tensors="pt", return_dict=True, **kwargs)
        except Exception as e:
            raise NonRetryableProviderError(f"chat template failed: {e}") from e
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}
        if request.seed is not None:
            torch.manual_seed(request.seed)
        do_sample = request.temperature > 0
        gen = dict(max_new_tokens=request.max_tokens, do_sample=do_sample)
        if do_sample:
            gen["temperature"] = request.temperature
            if request.top_p is not None:
                gen["top_p"] = request.top_p
        t0 = time.perf_counter()
        with torch.no_grad():
            out = self._model.generate(**inputs, **gen)
        latency = (time.perf_counter() - t0) * 1000.0
        n_in = inputs["input_ids"].shape[1]
        new = out[0][n_in:]
        text = self._tok.decode(new, skip_special_tokens=True)
        finish = "length" if len(new) >= request.max_tokens else "stop"
        return ChatResponse(
            text=text, finish_reason=finish,
            usage={"prompt_tokens": int(n_in), "completion_tokens": int(len(new))},
            latency_ms=round(latency, 1), logprobs=None,
            raw_metadata={"served_model": self.spec.model_id},
            request_params={"model": self.spec.model_id, **gen, "seed": request.seed,
                            "chat_template_kwargs": kwargs},
        )
