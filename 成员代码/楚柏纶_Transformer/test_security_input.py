import numpy as np

from config import CausalLMConfig
from model import CausalLM
from security_input import InputValidationError


def build_small_model():
    config = CausalLMConfig(
        vocab_size=10,
        hidden_size=8,
        num_layers=1,
        num_heads=2,
        max_position_embeddings=6,
    )
    model = CausalLM(config)
    model.embeddings = np.zeros((config.vocab_size, config.hidden_size))
    return model


def assert_raises_validation(func):
    try:
        func()
    except InputValidationError:
        return
    raise AssertionError("Expected InputValidationError")


def test_valid_forward_input():
    model = build_small_model()
    logits = model.forward([1, 2, 3])
    assert logits.shape == (3, model.config.vocab_size)


def test_rejects_negative_token_id():
    model = build_small_model()
    assert_raises_validation(lambda: model.forward([1, -1, 3]))


def test_rejects_out_of_vocab_token_id():
    model = build_small_model()
    assert_raises_validation(lambda: model.forward([1, 10, 3]))


def test_rejects_non_integer_token_id():
    model = build_small_model()
    assert_raises_validation(lambda: model.forward([1, "2", 3]))


def test_rejects_empty_input():
    model = build_small_model()
    assert_raises_validation(lambda: model.forward([]))


def test_rejects_overlong_input():
    model = build_small_model()
    assert_raises_validation(lambda: model.forward([1, 2, 3, 4, 5, 6, 7]))


def test_rejects_too_many_generated_tokens():
    model = build_small_model()
    assert_raises_validation(lambda: model.generate([1, 2, 3], max_new_tokens=4))


def test_valid_generation_length():
    model = build_small_model()
    output_ids = model.generate([1, 2, 3], max_new_tokens=2)
    assert len(output_ids) == 5


if __name__ == "__main__":
    tests = [
        test_valid_forward_input,
        test_rejects_negative_token_id,
        test_rejects_out_of_vocab_token_id,
        test_rejects_non_integer_token_id,
        test_rejects_empty_input,
        test_rejects_overlong_input,
        test_rejects_too_many_generated_tokens,
        test_valid_generation_length,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
