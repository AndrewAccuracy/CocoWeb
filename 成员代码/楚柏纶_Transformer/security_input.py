"""Input validation helpers for CausalLM inference."""


class InputValidationError(ValueError):
    """Raised when model input violates the inference safety policy."""


def _ensure_int(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputValidationError(f"{field_name} must be an integer")
    return value


def validate_input_ids(input_ids, vocab_size, max_position_embeddings):
    """Validate token ids before indexing the embedding matrix."""
    if not isinstance(input_ids, (list, tuple)):
        raise InputValidationError("input_ids must be a list or tuple of integers")

    if len(input_ids) == 0:
        raise InputValidationError("input_ids must not be empty")

    if len(input_ids) > max_position_embeddings:
        raise InputValidationError(
            f"input_ids length must not exceed {max_position_embeddings}"
        )

    safe_ids = []
    for index, token_id in enumerate(input_ids):
        token_id = _ensure_int(token_id, f"input_ids[{index}]")
        if token_id < 0 or token_id >= vocab_size:
            raise InputValidationError(
                f"input_ids[{index}] is outside the valid token range"
            )
        safe_ids.append(token_id)

    return safe_ids


def validate_max_new_tokens(max_new_tokens, max_position_embeddings, current_length):
    """Validate generation length before entering the autoregressive loop."""
    max_new_tokens = _ensure_int(max_new_tokens, "max_new_tokens")

    if max_new_tokens < 0:
        raise InputValidationError("max_new_tokens must not be negative")

    remaining = max_position_embeddings - current_length
    if max_new_tokens > remaining:
        raise InputValidationError(
            f"max_new_tokens must not exceed the remaining context length {remaining}"
        )

    return max_new_tokens
