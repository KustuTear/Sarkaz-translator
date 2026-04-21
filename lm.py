_LM_AVAILABLE = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    _LM_AVAILABLE = True
except ImportError:
    pass

MODEL_ID = "uer/gpt2-chinese-cluecorpussmall"
_cached_scorer = None


class LMScorer:
    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model


def build_lm_scorer(model_id: str = MODEL_ID) -> 'LMScorer | None':
    global _cached_scorer
    if not _LM_AVAILABLE:
        return None
    if _cached_scorer is not None:
        return _cached_scorer
    print(f'[*] 正在加载语言模型 {model_id}，首次运行需下载约 400MB...')
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    model.train(False)
    _cached_scorer = LMScorer(tokenizer, model)
    return _cached_scorer


def lm_score(text: str, scorer: 'LMScorer | None') -> float:
    if scorer is None or not text:
        return 0.0
    enc = scorer.tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
    input_ids = enc['input_ids']
    with torch.no_grad():
        loss = scorer.model(input_ids, labels=input_ids).loss
    return -loss.item()
