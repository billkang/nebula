# llm-provider Specification

## Purpose

Provide a unified, configurable LLM abstraction layer that Nebula platform modules can use to call AI capabilities without coupling to any specific LLM provider.

## ADDED Requirements

### Requirement: LLMProvider abstract interface

The system SHALL provide an abstract base class `LLMProvider` that defines the contract for all LLM provider implementations.

- **chat()**: synchronous text generation — accepts message list and optional system prompt, returns response string
- **chat_stream()**: streaming text generation — accepts same inputs, yields response content chunks
- Both methods SHALL accept `temperature` (default 0.3) and `max_tokens` (default 1024) parameters
- Both methods SHALL accept additional provider-specific kwargs via `**kwargs`

#### Scenario: Chat returns response string

- **WHEN** calling `provider.chat([{"role": "user", "content": "Hello"}])`
- **THEN** returns a non-empty string response

#### Scenario: Chat stream yields content chunks

- **WHEN** calling `provider.chat_stream([{"role": "user", "content": "Hello"}])`
- **THEN** yields one or more string chunks that concatenate to the full response

#### Scenario: System prompt is prepended to message list

- **WHEN** calling `provider.chat(messages, system_prompt="You are a translator")`
- **THEN** the system message is inserted at position 0 before the user messages

### Requirement: DeepSeek Provider implementation

The system SHALL include a `DeepSeekProvider` class that implements `LLMProvider` using DeepSeek's OpenAI-compatible API.

- **Default base_url**: `https://api.deepseek.com`
- **Default model**: `deepseek-chat`
- **Authentication**: via API key passed to constructor
- **SDK**: uses `openai` Python package (OpenAI-compatible client)

#### Scenario: DeepSeekProvider initializes with defaults

- **WHEN** creating `DeepSeekProvider(api_key="sk-xxx")`
- **THEN** internally creates an OpenAI client with base_url `https://api.deepseek.com` and model `deepseek-chat`

#### Scenario: DeepSeekProvider chat succeeds

- **WHEN** calling `chat()` with valid messages
- **THEN** returns the LLM response text via DeepSeek API

### Requirement: Factory function for global access

The system SHALL provide a `get_llm_provider()` factory function that returns a singleton LLM provider instance.

- **Configuration source**: reads `settings.llm_provider`, `settings.llm_api_key`, `settings.llm_model`, `settings.llm_base_url`
- **Provider resolution**: `"deepseek"` → `DeepSeekProvider`; any other value → `OpenAIClientProvider`
- **Singleton**: subsequent calls return the same instance without re-initializing
- **Reset**: a `reset_provider()` function SHALL be available for testing

#### Scenario: First call creates provider

- **WHEN** calling `get_llm_provider()` for the first time
- **THEN** initializes a new provider based on current settings and returns it

#### Scenario: Subsequent calls return same instance

- **WHEN** calling `get_llm_provider()` multiple times
- **THEN** returns the same provider instance

#### Scenario: Missing API key raises error

- **WHEN** `settings.llm_api_key` is empty and `get_llm_provider()` is called
- **THEN** raises `RuntimeError` with a message indicating the API key is not configured

### Requirement: Configuration via environment variables

The system SHALL support configuring the LLM provider through environment variables in `.env`.

- **DEEPSEEK_API_KEY**: API key for DeepSeek authentication (maps to `settings.llm_api_key`)
- **LLM_MODEL**: Model name override (default: `deepseek-chat`, maps to `settings.llm_model`)
- **LLM_BASE_URL**: API base URL override (default: `https://api.deepseek.com`, maps to `settings.llm_base_url`)
- **LLM_PROVIDER**: Provider type selection (default: `deepseek`, maps to `settings.llm_provider`)

#### Scenario: No API key configured

- **WHEN** `DEEPSEEK_API_KEY` is empty or missing in `.env`
- **THEN** `settings.llm_api_key` is empty string

#### Scenario: Custom model configured

- **WHEN** `.env` contains `LLM_MODEL=deepseek-reasoner`
- **THEN** `settings.llm_model` equals `"deepseek-reasoner"`

### Requirement: Change name translation via LLM

The system SHALL use the LLM provider to translate project names into English kebab-case identifiers for use as filesystem directory names and openspec change names.

- **Translation rules**: output SHALL be lowercase, words separated by hyphens, no spaces or special characters
- **Pinyin is NOT allowed**: "旅游助手" → "travel-assistant", NOT "lv-you-zhu-shou"
- **System prompt**: SHALL include clear translation rules with examples
- **Validation**: output SHALL be validated against kebab-case regex after translation; if invalid, retry once
- **Consistency**: the same project name SHALL produce the same change_name under the same model/temperature settings
- **Integration point**: `ProjectService.create_project()` SHALL call LLM before creating the DB record

#### Scenario: Chinese project name translated

- **WHEN** project name is "旅游助手"
- **THEN** change_name is "travel-assistant"

#### Scenario: English project name pass-through

- **WHEN** project name is "E-commerce Dashboard"
- **THEN** change_name is "e-commerce-dashboard"

#### Scenario: Invalid translation retried

- **WHEN** LLM returns "Travel Assistant" (uppercase + space)
- **THEN** system retries the translation with a retry instruction
- **AND** if retry also fails, raises an error and does NOT create the project

#### Scenario: LLM call fails

- **WHEN** the LLM API call fails (network error, timeout, auth error)
- **THEN** `create_project()` raises an appropriate error
- **AND** the project record is not created in DB
