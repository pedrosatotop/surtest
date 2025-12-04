# AI Brief Generator

A minimal, production-minded AI feature that generates campaign briefs for brands using OpenAI's GPT models. Built with Django and a clean, modern frontend.

## Documentation

### Prompt Design Choices

The prompt design follows a **two-part structure** for optimal results:

1. **System Prompt** (Concise and Deterministic):
   - Defines the AI's role as an expert marketing strategist
   - Sets clear constraints: "exactly 3 content angles and 3 creator selection criteria"
   - Specifies output length: "4-6 sentences" for briefs
   - Emphasizes platform-appropriateness and specificity

2. **User Prompt** (Compact and Structured):
   - Provides all inputs in a clear, structured format
   - Explicitly requests JSON output with specific fields
   - Uses the brand name and selected options directly

**Design Rationale:**
- **Separation of concerns**: System prompt defines behavior, user prompt provides context
- **Explicit structure**: Requesting JSON with named fields ensures consistent parsing
- **Deterministic constraints**: Specifying "exactly 3" items prevents variable-length arrays
- **Compact format**: Minimal tokens in prompts reduce cost while maintaining clarity

**Model Selection:**
- Using `gpt-4o-mini` for cost efficiency while maintaining quality
- Temperature set to `0.4` (below 0.5 requirement) for consistency
- `max_tokens: 600` to keep outputs concise and control costs
- `response_format: {"type": "json_object"}` forces structured output

### Guardrails Implemented

#### 1. **Input Validation (Allowlist-based)**
- **Platform**: Must be one of `["Instagram", "TikTok", "UGC"]`
- **Goal**: Must be one of `["Awareness", "Conversions", "Content Assets"]`
- **Tone**: Must be one of `["Professional", "Friendly", "Playful"]`
- **Brand Name**: 
  - Non-empty and trimmed
  - Minimum 2 characters, maximum 100 characters
  - Basic profanity filtering (extensible list)

#### 2. **LLM Call Safeguards**
- **Max Tokens**: 600 tokens limit to control cost and output length
- **Temperature**: 0.4 (≤ 0.5 as required) for deterministic, consistent outputs
- **Timeout**: 30 seconds to prevent hanging requests
- **JSON Schema Enforcement**: Using `response_format: {"type": "json_object"}` ensures structured output
- **Response Validation**: Checks that required fields exist and arrays have exactly 3 items

#### 3. **Rate Limiting**
- **In-memory rate limiter**: 10 requests per minute per IP address
- **Sliding window**: Tracks requests within 60-second windows
- **Graceful degradation**: Returns 429 status with remaining count
- **IP-based tracking**: Uses client IP from request headers

#### 4. **Error Handling**
- **JSON parsing errors**: Catches malformed responses
- **Validation errors**: Returns 400 with descriptive messages
- **Service errors**: Returns 500 with error details
- **Network timeouts**: Handled by OpenAI client timeout

#### 5. **Content Safety**
- **Profanity filter**: Basic word list (extensible for production)
- **Input sanitization**: Trims whitespace and validates length
- **Output structure validation**: Ensures response matches expected schema

### How Tokens and Latency Are Measured

#### Latency Measurement

Latency is measured using Python's `time` module:

```python
start_time = time.time()
# ... LLM API call ...
latency_ms = (time.time() - start_time) * 1000
```

- **Start time**: Captured immediately before the OpenAI API call
- **End time**: Captured immediately after receiving the response
- **Calculation**: Difference converted to milliseconds for readability
- **Included in response**: Rounded to 2 decimal places for precision

**What it measures:**
- Total round-trip time including network latency
- OpenAI API processing time
- JSON parsing time
- All overhead between request initiation and response receipt

#### Token Usage Measurement

Token usage is extracted directly from OpenAI's API response:

```python
tokens_used = response.usage.total_tokens
tokens_prompt = response.usage.prompt_tokens
tokens_completion = response.usage.completion_tokens
```

**Metrics tracked:**
- **Total tokens**: Complete request + response token count
- **Prompt tokens**: Input tokens (system + user prompts)
- **Completion tokens**: Output tokens (generated brief)
- **Estimated cost**: Calculated using approximate pricing for gpt-4o-mini ($0.15 per 1M input tokens, $0.60 per 1M output tokens)

**Cost calculation:**
```python
estimated_cost_usd = (tokens_prompt * 0.15 + tokens_completion * 0.60) / 1_000_000
```

**Why this approach:**
- Uses OpenAI's built-in token counting (most accurate)
- Separates prompt vs completion for cost analysis
- Provides visibility into where tokens are consumed
- Helps optimize prompts for cost efficiency

#### Telemetry in Response

All metrics are included in the JSON response under the `telemetry` key:
- Frontend can display these metrics to users
- Enables monitoring and debugging
- Provides cost transparency

### Loom Demo

https://www.loom.com/share/7b9e280605bd429b99cae3c0cfd7f519

