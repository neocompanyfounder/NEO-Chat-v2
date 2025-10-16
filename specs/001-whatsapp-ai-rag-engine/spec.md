# Feature Specification: NEO Chat WhatsApp AI RAG Engine

**Feature Branch**: `001-whatsapp-ai-rag-engine`  
**Created**: 2025-01-16  
**Status**: Draft  
**Input**: User description: "NEO Chat's AI engine utilizes a flexible agent framework powered by CrewAI for task automation, enabling multi-agent orchestration with custom functions and structured outputs. It integrates with the Google Gemini API, specifically using the Flash 2.5 model, for high-speed LLM inference. A personalized knowledge base is built through a per-user RAG pipeline that ingests, chunks, embeds, and stores user-uploaded files in a Supabase self-hosted vector database, grounding responses in user-specific data. For web-based knowledge, the Crawl4AI web crawler integrates to asynchronously process and feed website content into the RAG ingestion pipeline, enriching the user's knowledge base and fostering customized AI assistants. The knowledge base also incorporates all chat history, which is memorized, and users have the option to reset their knowledge base. NEO Chat is based on a WhatsApp number: A core requirement is to connect a personal WhatsApp number to the backend without directly managing it through the Meta Business Suite. It will use the Evolution API, an open-source project that can serve as a connector to the official WhatsApp Cloud API. While intriguing, relying on an open-source intermediary for a core business function may introduce support and maintenance risks compared to a commercially backed BSP. The design must leverage native interactive message components, with List Messages used for menus with up to 10 options (e.g., main menu actions), Reply Buttons for up to 3 quick, contextual choices (e.g., Yes/No, sub-menu navigation), and Text Input for all free-form text. The user can send text, voice, images that are received through whatsapp."

## Clarifications

### Session 2025-01-16

- Q: How should the system authenticate users and protect their knowledge bases from unauthorized access? → A: WhatsApp phone number is the sole authentication mechanism; Evolution API validates sender identity
- Q: What chunking strategy and size should be used for the RAG pipeline? → A: Semantic chunking by paragraphs/sections (variable size, 100-2000 tokens)
- Q: What is the maximum crawl depth for website processing? → A: Unlimited depth until 100 pages reached or domain boundary
- Q: Which voice transcription service should be used for voice message processing? → A: Google Cloud Speech-to-Text API (integrates with existing Google Gemini usage)
- Q: What specific file formats should be supported for upload? → A: Comprehensive office suite (PDF, TXT, DOCX, XLSX, PPTX, images)
- Q: Which embedding model should be used for generating text chunk embeddings? → A: Gemini embeddings (text-embedding-004 or latest) with Supabase vector database for similarity search
- Q: Which agent framework should be used for AI task automation? → A: CrewAI framework for multi-agent orchestration and task automation

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Basic WhatsApp Text Conversation (Priority: P1)

A user sends a text message to the NEO Chat WhatsApp number and receives an AI-generated response based on their personal knowledge base. The conversation history is automatically saved to the user's knowledge base for future context.

**Why this priority**: This is the core MVP functionality. Without basic text conversation, no other features can function. It validates the entire WhatsApp integration, AI engine, and knowledge base pipeline.

**Independent Test**: Send a text message via WhatsApp to the bot number, receive a contextual AI response within 10 seconds, and verify the conversation is stored in the user's knowledge base.

**Acceptance Scenarios**:

1. **Given** a user has the NEO Chat WhatsApp number saved, **When** they send "Hello, what can you help me with?", **Then** they receive an AI-generated greeting explaining the bot's capabilities within 10 seconds
2. **Given** a user has previous chat history, **When** they ask "What did we discuss yesterday?", **Then** the AI retrieves and summarizes previous conversations from their knowledge base
3. **Given** a user sends a message, **When** the AI responds, **Then** the entire conversation (user message + AI response) is stored in the user's knowledge base
4. **Given** a user sends multiple messages in quick succession, **When** the AI processes them, **Then** each message receives a response in the order received

---

### User Story 2 - File Upload and Knowledge Base Enrichment (Priority: P2)

A user uploads a document (PDF, Word, Excel, PowerPoint, text file, or image with text) via WhatsApp, and the system ingests it into their personal knowledge base. The AI can then answer questions about the uploaded content.

**Why this priority**: This enables personalized AI assistance grounded in user-specific data. It's the key differentiator that makes NEO Chat a customized assistant rather than a generic chatbot.

**Independent Test**: Upload a PDF document via WhatsApp, ask a question about its content, and verify the AI responds with information extracted from the uploaded file.

**Acceptance Scenarios**:

1. **Given** a user has a PDF document, **When** they send it via WhatsApp with caption "Please analyze this report", **Then** the system confirms receipt, processes the file, and stores it in their knowledge base within 30 seconds
2. **Given** a user has uploaded a document about project requirements, **When** they ask "What are the key deliverables mentioned in my document?", **Then** the AI retrieves relevant information from the uploaded file and provides an accurate summary
3. **Given** a user uploads an image containing text (screenshot, photo of document), **When** the system processes it, **Then** the text is extracted and stored in their knowledge base
4. **Given** a user uploads multiple files over time, **When** they ask a question, **Then** the AI searches across all uploaded documents to provide comprehensive answers

---

### User Story 3 - Web Content Crawling and Integration (Priority: P3)

A user shares a website URL via WhatsApp, and the system crawls the web content, processes it, and adds it to their knowledge base. The AI can then answer questions about the website content.

**Why this priority**: Extends the knowledge base beyond uploaded files to include web-based information, making the assistant more versatile. This is valuable but not essential for MVP.

**Independent Test**: Send a website URL via WhatsApp, wait for crawling confirmation, then ask a question about the website content and verify the AI responds with accurate information from the crawled pages.

**Acceptance Scenarios**:

1. **Given** a user finds a useful article online, **When** they send the URL via WhatsApp, **Then** the system confirms it will crawl the site and notifies them when processing is complete
2. **Given** a user has shared a documentation website URL, **When** the crawling completes, **Then** the AI can answer questions about the documentation content
3. **Given** a website has multiple pages, **When** the system crawls it, **Then** it processes all linked pages within the same domain up to 100 pages maximum and stores the content in the user's knowledge base
4. **Given** a user shares a URL to a page with dynamic content, **When** the system crawls it, **Then** it captures the rendered content including JavaScript-generated text

---

### User Story 4 - Voice Message Processing (Priority: P4)

A user sends a voice message via WhatsApp, and the system transcribes it to text, processes it through the AI engine, and responds with both text and optionally voice.

**Why this priority**: Enhances user experience by supporting voice interaction, which is common in WhatsApp usage. This is a convenience feature that can be added after core text functionality is stable.

**Independent Test**: Send a voice message asking a question, receive a text response based on the transcribed content, and verify the transcription accuracy.

**Acceptance Scenarios**:

1. **Given** a user records a voice message asking "What's the weather like today?", **When** they send it, **Then** the system transcribes the audio, processes the question, and responds with text
2. **Given** a user sends a voice message, **When** the transcription completes, **Then** the transcribed text is stored in the conversation history in their knowledge base
3. **Given** a user sends a voice message in a noisy environment, **When** the system transcribes it, **Then** it handles background noise gracefully and provides the best possible transcription
4. **Given** a voice message contains multiple sentences, **When** the AI processes it, **Then** it understands the full context and responds appropriately

---

### User Story 5 - Interactive Menu Navigation (Priority: P5)

A user interacts with the AI using WhatsApp's native interactive components (List Messages for menus, Reply Buttons for quick choices) to navigate features and perform actions.

**Why this priority**: Improves user experience with structured interactions, making the bot more intuitive. This is a UX enhancement that can be added after core conversational AI works.

**Independent Test**: Send a command to trigger the main menu, receive a List Message with options, select an option, and verify the appropriate action is taken.

**Acceptance Scenarios**:

1. **Given** a user sends "/menu" or "menu", **When** the system responds, **Then** it sends a List Message with up to 10 main menu options (e.g., "Upload File", "Crawl Website", "Reset Knowledge Base", "Help")
2. **Given** a user selects "Reset Knowledge Base" from the menu, **When** the system processes it, **Then** it sends Reply Buttons with "Yes" and "No" options for confirmation
3. **Given** a user confirms an action with a Reply Button, **When** the system executes it, **Then** it provides feedback on the action's success or failure
4. **Given** a user is in a multi-step workflow, **When** they use Reply Buttons to navigate, **Then** the system maintains context and guides them through the process

---

### User Story 6 - Knowledge Base Reset (Priority: P6)

A user can reset their entire knowledge base, clearing all uploaded files, crawled web content, and conversation history, starting fresh with the AI.

**Why this priority**: Provides users control over their data and allows them to start over if needed. This is important for privacy and data management but not critical for initial launch.

**Independent Test**: Request a knowledge base reset, confirm the action, and verify all previous context is cleared when asking the AI a question that previously had context.

**Acceptance Scenarios**:

1. **Given** a user has an established knowledge base, **When** they send "reset my knowledge base", **Then** the system asks for confirmation via Reply Buttons
2. **Given** a user confirms the reset, **When** the system processes it, **Then** all uploaded files, crawled content, and conversation history are permanently deleted from their knowledge base
3. **Given** a user has reset their knowledge base, **When** they ask a question that previously had context, **Then** the AI responds without any prior knowledge, confirming the reset was successful
4. **Given** a user resets their knowledge base, **When** they start a new conversation, **Then** the system treats them as a new user with no history

### Edge Cases

- **What happens when a user sends an extremely large file (>100MB)?** System should reject files above a size limit (e.g., 25MB for WhatsApp) and notify the user with the maximum allowed size
- **What happens when a user sends a corrupted or unsupported file format?** System should detect the issue, notify the user that the file cannot be processed, and suggest supported formats
- **What happens when the AI inference service (Gemini API) is temporarily unavailable?** System should queue the message, retry with exponential backoff, and notify the user if the delay exceeds 60 seconds
- **What happens when a user sends messages faster than the system can process them?** System should queue messages and process them in order, sending a "processing your request" acknowledgment immediately
- **What happens when a website URL cannot be crawled (403 Forbidden, 404 Not Found, timeout)?** System should notify the user of the specific error and suggest alternatives (e.g., "This website blocks automated access. Try uploading a PDF instead.")
- **What happens when a voice message is in an unsupported language or has very poor audio quality?** System should attempt transcription, notify the user if confidence is low, and ask them to resend or type the message
- **What happens when multiple users share the same WhatsApp number?** Each user should have a separate knowledge base identified by their WhatsApp phone number (sender ID)
- **What happens when the vector database is full or unavailable?** System should gracefully degrade, notify administrators, and inform the user that knowledge base operations are temporarily unavailable
- **What happens when a user's knowledge base grows extremely large (>10GB)?** System should implement pagination, archiving, or limits, and notify the user when approaching storage limits
- **What happens when the Evolution API connection is lost?** System should attempt to reconnect automatically, log the outage, and notify administrators if the connection cannot be restored within 5 minutes

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

#### WhatsApp Integration

- **FR-001**: System MUST connect to a personal WhatsApp number via the Evolution API without requiring Meta Business Suite management
- **FR-002**: System MUST receive text messages, voice messages, images, and files sent to the WhatsApp number
- **FR-003**: System MUST send text responses back to users via WhatsApp
- **FR-004**: System MUST support WhatsApp List Messages for menus with up to 10 options
- **FR-005**: System MUST support WhatsApp Reply Buttons for up to 3 quick choices
- **FR-006**: System MUST identify each user by their unique WhatsApp phone number (sender ID)

#### AI Engine

- **FR-007**: System MUST use CrewAI framework for multi-agent orchestration and task automation
- **FR-008**: System MUST integrate with Google Gemini Flash 2.5 model for LLM inference
- **FR-009**: System MUST support custom functions and structured outputs in AI responses
- **FR-010**: System MUST generate responses within 10 seconds for text queries under normal load
- **FR-011**: System MUST handle concurrent requests from multiple users without blocking

#### Knowledge Base & RAG Pipeline

- **FR-012**: System MUST maintain a separate knowledge base for each user identified by WhatsApp phone number
- **FR-013**: System MUST ingest uploaded files (PDF, TXT, DOCX, XLSX, PPTX, JPG, PNG, WEBP) and extract text content
- **FR-014**: System MUST chunk extracted text into semantically meaningful segments using paragraph/section boundaries with variable size (100-2000 tokens per chunk)
- **FR-015**: System MUST generate embeddings for text chunks using Google Gemini embedding model (text-embedding-004 or latest)
- **FR-016**: System MUST store embeddings and text chunks in a Supabase self-hosted vector database
- **FR-017**: System MUST perform vector similarity search to retrieve relevant context for user queries
- **FR-018**: System MUST store all conversation history (user messages and AI responses) in the user's knowledge base
- **FR-019**: System MUST support knowledge base reset functionality, permanently deleting all user data upon confirmation

#### Web Crawling

- **FR-020**: System MUST integrate Crawl4AI web crawler for asynchronous website content processing with unlimited depth until 100 pages or domain boundary is reached
- **FR-021**: System MUST extract text content from crawled web pages
- **FR-022**: System MUST process crawled content through the same RAG ingestion pipeline as uploaded files
- **FR-023**: System MUST handle crawling errors gracefully and notify users of failures
- **FR-024**: System MUST respect robots.txt and implement rate limiting to avoid overloading target websites

#### Voice Processing

- **FR-025**: System MUST transcribe voice messages to text using Google Cloud Speech-to-Text API
- **FR-026**: System MUST process transcribed text through the AI engine and knowledge base
- **FR-027**: System MUST store transcribed voice messages in conversation history

#### Data Management

- **FR-028**: System MUST persist all user knowledge bases across system restarts
- **FR-029**: System MUST implement data isolation ensuring users cannot access other users' knowledge bases
- **FR-030**: System MUST log all user interactions for debugging and analytics
- **FR-031**: System MUST implement error handling and retry logic for external API failures (Gemini, Evolution API, Supabase)

#### Security & Authentication

- **FR-032**: System MUST authenticate users solely by their WhatsApp phone number as validated by the Evolution API
- **FR-033**: System MUST trust the Evolution API's sender identity validation without additional authentication layers
- **FR-034**: System MUST ensure each user's knowledge base is accessible only via their authenticated WhatsApp phone number

### Key Entities

- **User**: Represents a WhatsApp user interacting with NEO Chat. Identified by WhatsApp phone number. Has one knowledge base. Sends messages and receives AI responses.

- **Knowledge Base**: A per-user collection of all ingested content. Contains uploaded files, crawled web content, and conversation history. Supports vector similarity search. Can be reset by the user.

- **Message**: Represents a single communication unit. Can be text, voice, image, or file. Has a sender (user or AI), timestamp, content, and message type. Stored in conversation history.

- **Document**: Represents uploaded or crawled content. Has source (file upload or web URL), raw content, processed chunks, embeddings, and metadata (upload date, file type, size).

- **Chunk**: A semantically meaningful segment of text extracted from a document. Has parent document reference, text content, embedding vector, and position in original document.

- **Conversation**: A chronological sequence of messages between a user and the AI. Belongs to a user's knowledge base. Used for context retrieval and history display.

- **AI Agent**: Represents the CrewAI agent instance. Has custom tools, roles, goals, and access to user's knowledge base. Generates responses based on user queries and retrieved context through multi-agent collaboration.

- **Crawl Job**: Represents a web crawling task. Has target URL, crawl status (pending, in-progress, completed, failed), crawled pages count, and completion timestamp.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users receive AI responses to text messages within 10 seconds under normal load (95th percentile)
- **SC-002**: System successfully processes and stores uploaded files in knowledge base within 30 seconds for files up to 10MB
- **SC-003**: AI responses demonstrate accurate retrieval from user's knowledge base with 90% relevance score on test queries
- **SC-004**: System handles at least 100 concurrent users without response time degradation beyond 15 seconds
- **SC-005**: Voice message transcription accuracy achieves 85% word-level accuracy for clear audio in supported languages
- **SC-006**: Web crawling completes for standard documentation sites (up to 100 pages) within 5 minutes
- **SC-007**: Knowledge base reset operation completes within 10 seconds and successfully removes all user data
- **SC-008**: System maintains 99% uptime for WhatsApp message reception and AI response generation
- **SC-009**: 90% of users successfully complete their first interaction (send message, receive response) without errors
- **SC-010**: System successfully recovers from Evolution API disconnections within 5 minutes without data loss
