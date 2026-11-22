# Study guide for Exam AI-200: Developing AI Cloud Solutions on Azure

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200
Retrieved: 2026-11-23

## Purpose of this document

This study guide should help you understand what to expect on the exam and includes a summary of the topics the exam might cover and links to additional resources. The information and materials in this document should help you focus your studies as you prepare for the exam.

| Useful links | Description |
|---|---|
| [Certification renewal](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification) | Microsoft associate, expert, and specialty certifications expire annually. You can renew by passing a **free** online assessment on Microsoft Learn. |
| [Your Microsoft Learn profile](https://learn.microsoft.com/en-us/users) | Connecting your certification profile to Microsoft Learn allows you to schedule and renew exams and share and print certificates. |
| [Exam scoring and score reports](https://learn.microsoft.com/en-us/credentials/certifications/exam-scoring-reports) | A score of 700 or greater is required to pass. |
| [Exam sandbox](https://aka.ms/examdemo) | You can explore the exam environment by visiting our exam sandbox. |
| [Request accommodations](https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations) | If you use assistive devices, require extra time, or need modification to any part of the exam experience, you can request an accommodation. |

## About the exam

Some exams are localized into other languages, and those are updated approximately eight weeks after the English version is updated. If the exam isn't available in your preferred language, you can request an additional 30 minutes to complete the exam.

The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured

### Audience profile

As a candidate for this Microsoft Certification, you’re responsible for contributing to all phases of implementing AI solutions on Azure, with an emphasis on back-end services and components. You’re also responsible for supporting all phases of the development lifecycle, including requirements gathering, design, development, deployment, security, and monitoring.

You should be proficient in:

- Azure SDKs and third-party SDKs used in Azure.
- Azure data management services.
- Azure monitoring and troubleshooting.
- Azure messaging and eventing.
- Vector databases.
- Python programming.
- Implementing containerized applications on Azure.

### Skills at a glance

- Develop containerized solutions on Azure (20–25%)
- Develop AI solutions by using Azure data management services (25–30%)
- Connect to and consume Azure services (20–25%)
- Secure, monitor, troubleshoot Azure solutions (20–25%)

Skills measured

NOTE: The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

NOTE: Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

### Develop containerized solutions on Azure (20–25%)

#### Implement container application hosting

- Build, store, version, and manage container images by using Azure Container Registry
- Build and run images by using Azure Container Registry Tasks
- Deploy containers to Azure App Service, including configuring App Service to supply environment variables and secrets

#### Implement container-orchestrated solutions

- Deploy applications to Azure Container Apps, including environment configuration and revision management
- Implement event-driven scaling by using Kubernetes Event‑driven Autoscaling (KEDA) in Container Apps
- Deploy and manage applications to Azure Kubernetes Service (AKS) by using manifest files
- Monitor and troubleshoot solutions on AKS and Container Apps by inspecting logs, events, and end-to-end connectivity

### Develop AI solutions by using Azure data management services (25–30%)

#### Develop AI solutions by using Azure Cosmos DB for NoSQL

- Connect to Azure Cosmos DB for NoSQL by using the SDK and run queries
- Optimize query performance and Request Units (RUs) consumption by using indexing policies and consistency levels
- Store and retrieve embeddings and execute vector similarity search for semantic retrieval
- Implement a change feed processor to detect and handle new or updated items

#### Develop AI solutions by using Azure Database for PostgreSQL

- Connect and query Azure Database for PostgreSQL by using SDKs
- Model schemas and implement indexing strategies, including designing tables and choosing appropriate data types
- Implement indexing strategies, including optimizing query latency and reducing pgvector compute overhead
- Configure compute, memory, and storage resources to support vector workloads
- Run vector similarity search, including storing embeddings, semantic retrieval, and implementing retrieval-augmented generation (RAG) patterns by using metadata filter
- Implement connection optimization to improve throughput and minimize latency

#### Integrate Azure Managed Redis in AI solutions

- Implement Azure Managed Redis data operations, including caching, expiration, and invalidation
- Implement vector indexing to enable similarity search

### Connect to and consume Azure services (20–25%)

#### Develop event- and message-based AI solutions

- Queue and process back-end operations by using Azure Service Bus, including dead-letter queue handling, messages, topics, and subscriptions
- Implement event-driven workflows by using Azure Event Grid, including filters, custom events, and retries

#### Develop and implement Azure Functions

- Build serverless APIs, including implementing triggers and bindings
- Configure and deploy function apps

### Secure, monitor, and troubleshoot Azure solutions (20–25%)

#### Implement secure Azure solutions

- Secure secrets by using Azure Key Vault, including rotation and retrieval
- Store and retrieve app configuration information by using Azure App Configuration

#### Monitor and troubleshoot Azure solutions

- Trace distributed systems by using OpenTelemetry SDKs
- Write KQL queries to analyze logs and metrics

## Study resources

We recommend that you train and get hands-on experience before you take the exam. We offer self-study options and classroom training as well as links to documentation, community sites, and videos.

| Study resources | Links to learning and documentation |
|---|---|
| Get trained | [Choose from self-paced learning paths and modules or take an instructor-led course](https://learn.microsoft.com/en-us/credentials/certifications/exams/az-204#two-ways-to-prepare) |
| Find documentation | [Azure documentation](https://learn.microsoft.com/en-us/azure/?product=featured)[Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)[Container Instances](https://learn.microsoft.com/en-us/azure/container-instances/)[App Service](https://learn.microsoft.com/en-us/azure/app-service/)[Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/)[Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/)[Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/)[Microsoft Entra ID](https://learn.microsoft.com/en-us/azure/active-directory/)[Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/)[Azure Cache for Redis](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/)[API Apps](https://learn.microsoft.com/en-us/azure/app-service/)[API Management](https://learn.microsoft.com/en-us/azure/api-management/)[Event Hubs](https://learn.microsoft.com/en-us/azure/event-hubs/)[Event Grid](https://learn.microsoft.com/en-us/azure/event-grid/)[Service Bus Messaging](https://learn.microsoft.com/en-us/azure/service-bus-messaging/)[Queue Storage](https://learn.microsoft.com/en-us/azure/storage/queues/) |
| Ask a question | [Microsoft Q&A \| Microsoft Docs](https://learn.microsoft.com/en-us/answers/products/) |
| Get community support | [Azure Community Support](https://azure.microsoft.com/support/community/) |
| Follow Microsoft Learn | [Microsoft Learn - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/microsoft-learn/ct-p/MicrosoftLearn) |
| Find a video | [Watch the Exam Prep video](https://aka.ms/AI200-ExamPrep)[Azure Fridays](https://azure.microsoft.com/resources/videos/azure-friday/)[Browse other Microsoft Learn shows](https://learn.microsoft.com/en-us/shows/browse) |
