# model.py
import numpy as np
from config import CausalLMConfig
from transformer_block import TransformerBlock
from layernorm import LayerNorm

class CausalLM:
    def __init__(self, config: CausalLMConfig):
        self.config = config
        self.embeddings = np.random.randn(config.vocab_size, config.hidden_size) * 0.01
        self.blocks = [
            TransformerBlock(config.hidden_size, config.num_heads, config.dropout)
            for _ in range(config.num_layers)
        ]
        self.ln_f = LayerNorm(config.hidden_size)
        self.head = np.random.randn(config.hidden_size, config.vocab_size) * 0.01

    def forward(self, input_ids):
        # input_ids: [seq_len]
        x = self.embeddings[input_ids]  # [seq_len, hidden_size]
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits = x @ self.head  # [seq_len, vocab_size]
        return logits

    def generate(self, input_ids, max_new_tokens=20):
        ids = list(input_ids)
        for _ in range(max_new_tokens):
            logits = self.forward(ids)
            next_id = int(np.argmax(logits[-1]))
            ids.append(next_id)
        return ids
