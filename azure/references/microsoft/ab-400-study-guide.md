# Study guide for Exam AB-400: Extending Microsoft Power Platform Solutions with Code and AI

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ab-400
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

## Updates to the exam

Our exams are updated periodically to reflect skills that are required to perform a role. We have included two versions of the Skills Measured objectives depending on when you are taking the exam.

We always update the English language version of the exam first. Some exams are localized into other languages, and those are updated approximately eight weeks after the English version is updated. While Microsoft makes every effort to update localized versions as noted, there may be times when the localized versions of an exam are not updated on this schedule. Other available languages are listed in the **Schedule Exam** section of the **Exam Details** webpage. If the exam isn't available in your preferred language, you can request an additional 30 minutes to complete the exam.

The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured

### Audience profile

As a candidate for this exam, you design, develop, test, and troubleshoot solution components by using the extension points of Microsoft Power Platform and generative AI. You implement:

- custom user experiences and business logic.
- system integrations.
- data conversions.
- custom process automation.
- Power Automate workflow expressions.
- agentic AI as part of your solution logic.

You must have applied knowledge of:

- Microsoft Power Platform services, including an in-depth understanding of its capabilities, boundaries, and constraints.
- authentication, security, and application lifecycle management (ALM) practices for the Microsoft Power Platform.
- Microsoft Power Platform developer tools, including Microsoft Power Platform CLI as part of the development workflow.
- AI assisted tools and agents to enhance solution development and troubleshooting.
- modern IDE and developer productivity tools, such as Microsoft Visual Studio and Visual Studio Code.

You have development experience with:

- Microsoft Power Platform services
- JavaScript, JSON, TypeScript, and Power Fx
- C#, Python, HTML, and YAML
- RESTful Web APIs
- Microsoft Azure
- Microsoft Foundry
- Microsoft Copilot Studio

### Skills at a glance

- Build Microsoft Power Platform solutions (15–20%)
- Extend the user experience (25–30%)
- Extend Microsoft Power Platform (35–40%)
- Develop integrations (10–15%)

### Build Microsoft Power Platform solutions (15–20%)

#### Design the technical architecture

- Analyze the technical architecture to identify solution components and their implementation approach
- Design authentication and authorization for solution components
- Determine whether requirements can be met with out-of-the-box functionality
- Determine where to implement business logic including cloud services, client-side processing, business rules, plug-ins, and automation
- Determine when to use standard tables, virtual tables, elastic tables, or connectors
- Assess the impact of Microsoft Power Platform security features on solution components, including managed environments, data policies, security roles, teams, business units, and row sharing
- Determine when to use deterministic or non-deterministic methods to implement business logic
- Determine when to use code apps, generative pages, Power Apps component frameworks (PCFs), web resources, interactive agents, and Model Context Protocol (MCP) app widgets to implement the user experience
- Determine when to use Microsoft Foundry or Microsoft Copilot Studio to build agents

#### Design solution components

- Design Power Apps reusable components including generative pages, code components (PCF), and client scripting
- Design custom connectors and MCP servers for use with Microsoft Power Platform solutions
- Design Dataverse code components, including plug-ins and custom APIs
- Design automations, including Power Automate cloud flows and Copilot Studio workflows
- Design inbound and outbound integrations using Dataverse and Microsoft Azure
- Design custom interfaces by using Power Apps code apps
- Design custom agents that integrate with Microsoft Power Platform
- Design monitoring and alerting, including Azure Monitor Application Insights and Microsoft Power Platform monitor alerts

#### Implement application lifecycle management (ALM)

- Manage solution dependencies
- Create and use environment variables
- Manage solution layers

- Implement and extend Microsoft Power Platform Pipelines

- Create Continuous Integration/Continuous Deployment (CI/CD) automations using Microsoft Power Platform Build Tools

### Extend the user experience (25–30%)

#### Apply business logic in model-driven apps by using client scripting

- Build code that targets the Client API object model
- Determine an event handler registration approach
- Create client scripting that targets the Dataverse Web API
- Configure commands and buttons by using Power Fx and JavaScript
- Implement navigation, dialogs, and notifications by using the Client API

#### Create PCF code components

- Demonstrate the use of the different lifecycle events
- Configure a code component manifest
- Implement component interfaces
- Package, deploy, and consume a component
- Configure and use Device, Utility, and Web API features in component logic

#### Build Power Apps code apps

- Configure code apps to use Microsoft Power Platform connections
- Configure code apps to use Dataverse tables
- Perform table and metadata operations on Dataverse data
- Perform Dataverse actions and functions
- Configure code apps to use Power Automate cloud flows
- Configure code apps to use agents built in Copilot Studio
- Configure code apps to use environment variables

#### Deploy and manage Power Apps code apps

- Configure Content Security Policy (CSP) settings
- Implement monitoring by using Azure Application Insights
- Package, deploy, and share code apps
- Troubleshoot code apps by using Monitor and other browser-based debugging tools
- Optimize code app performance and resource usage

### Extend Microsoft Power Platform (35–40%)

#### Create a Dataverse plug-in

- Demonstrate the use of the different event execution pipeline stages
- Develop a plug-in that uses the execution context
- Develop a plug-in that implements business logic
- Implement images to support plug-in logic
- Perform operations in plug-ins by using the Organization service
- Optimize plug-in performance
- Configure a Dataverse custom API message
- Register plug-in components by using the Plug-in Registration Tool
- Develop a plug-in that implements a custom API
- Configure Dataverse business events
- Configure Microsoft Power Platform managed identity for plug-ins

#### Perform operations by using platform APIs

- Perform operations by using the Dataverse Web API
- Perform operations by using the Organization service
- Implement API limit retry policies
- Optimize solution components for performance, concurrency, transactions, and bulk operations
- Implement and troubleshoot authentication by using OAuth
- Perform asynchronous logic by using background operations
- Perform operations by using Dataverse SDKs for .NET and Python

#### Process workloads by using Microsoft Azure Functions

- Process long-running operations by using Azure Functions for Microsoft Power Platform solutions
- Implement scheduled and event-driven triggers in Azure Functions for Microsoft Power Platform solutions
- Authenticate to Microsoft Power Platform by using managed identities

#### Configure Power Automate cloud flows and Copilot Studio workflows

- Implement complex expressions in flow steps
- Implement flow control actions including error handling
- Configure trigger filter and retry policies
- Develop reuseable logic by using child flows
- Implement authentication for the Dataverse connector by using service principals

#### Build Microsoft Foundry agents by using code that integrates with the Microsoft Power Platform

- Integrate custom agents by using Microsoft Power Platform MCP servers
- Connect custom agents to Copilot Studio agents
- Integrate custom agents with Dataverse data by using Work IQ
- Consume Copilot Studio agents by using the Copilot Studio client library

### Develop integrations (10–15%)

#### Publish and consume Dataverse events

- Publish a Dataverse event by using the IServiceEndpointNotificationService
- Publish a Dataverse event by using the Plug-in Registration Tool
- Register service endpoints including webhooks, Azure Service Bus, and Azure Event Hub
- Recommend options for listening to Dataverse events

#### Implement synchronization for Dataverse data

- Perform data synchronization by using change tracking
- Develop code that uses alternate keys
- Synchronize data by using the UpsertRequest message

#### Create custom connectors

- Implement authentication for custom connectors
- Configure policy templates to modify connector behavior at runtime
- Import definitions from existing APIs including Open API definitions, Azure services, and GitHub
- Create a custom connector for an Azure service
- Develop an Azure Function to be used in a custom connector
- Extend the Open API definition for a custom connector
- Develop code for a custom connector to transform data

## Study resources

We recommend that you train and get hands-on experience before you take the exam. We offer self-study options and classroom training as well as links to documentation, community sites, and videos.

| Study resources | Links to learning and documentation |
|---|---|
| Get trained | [Choose from self-paced learning paths and modules or take an instructor-led course](https://learn.microsoft.com/en-us/credentials/certifications/exams/PL-400#two-ways-to-prepare) |
| Find documentation | [Developer learning catalog - Power Apps](https://learn.microsoft.com/en-us/power-apps/learning-catalog/developer)[Planning a Power Apps project](https://learn.microsoft.com/en-us/power-apps/guidance/planning/introduction)[Canvas apps](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/)[Model-driven apps](https://learn.microsoft.com/en-us/power-apps/maker/model-driven-apps/)[Power Pages](https://learn.microsoft.com/en-us/power-pages/)[Microsoft Dataverse](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-intro)[Tables and metadata](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/create-edit-metadata)[Dataverse developer](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/)[Model-driven apps developer](https://learn.microsoft.com/en-us/power-apps/developer/model-driven-apps/)[Canvas apps developer](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/dev-enterprise-intro)[Implement healthy ALM using solutions](https://learn.microsoft.com/en-us/power-platform/alm/overview-alm)[Use Microsoft Power Platform Build Tools](https://learn.microsoft.com/en-us/power-platform/alm/devops-build-tools) |
| Ask a question | [Microsoft Q&A \| Microsoft Docs](https://learn.microsoft.com/en-us/answers/products/) |
| Get community support | [Power Apps - Power Platform Community](https://powerusers.microsoft.com/t5/Power-Apps-Community/ct-p/PowerApps1) [Microsoft Power Automate - Power Platform Community](https://powerusers.microsoft.com/t5/Microsoft-Power-Automate/ct-p/MPACommunity) |
| Follow Microsoft Learn | [Microsoft Learn - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/microsoft-learn/ct-p/MicrosoftLearn) |
| Find a video | [Course Videos on YouTube](https://www.youtube.com/@MicrosoftLearn)[Browse other Microsoft Learn shows](https://learn.microsoft.com/en-us/shows/browse) |

## Change log

The table below summarizes the changes between the current and previous version of the skills measured. The functional groups are in bold typeface followed by the objectives within each group. The table is a comparison between the previous and current version of the exam skills measured and the third column describes the extent of the changes.

| Skill area prior to October 16, 2026 | Skill area as of October 16, 2026 | Change |
|---|---|---|
| Audience profile |  | Minor |
| Create a technical design |  | Removed |
| Design technical architecture |  | Moved |
| Design solution components |  | Moved |
| **Build Power Platform solutions** | **Build Microsoft Power Platform solutions** | % increased |
|  | Design the technical architecture | Major |
|  | Design solution components | Major |
| Configure and troubleshoot Microsoft Power Platform |  | Removed |
| Implement application lifecycle management (ALM) | Implement application lifecycle management (ALM) | Major |
| Implement Power Apps improvements |  | Removed |
| Implement advanced canvas apps features |  | Removed |
| Optimize and troubleshoot apps |  | Removed |
| **Extend the user experience** | **Extend the user experience** | % increased |
| Apply business logic in model-driven apps using client scripting | Apply business logic in model-driven apps by using client scripting | Minor |
| Create a Power Apps component framework (PCF) code component | Create PCF code components | Minor |
|  | Build Power Apps code apps | New |
|  | Deploy and manage Power Apps code apps | New |
| **Extend the platform** | **Extend Microsoft Power Platform** | % increased |
| Create a Dataverse plug-in | Create a Dataverse plug-in | Minor |
| Create custom connectors |  | Moved |
| Use platform APIs | Perform operations by using platform APIs | Major |
| Process workloads by using Azure Functions | Process workloads by using Microsoft Azure Functions | No change |
| Configure Power Automate cloud flows | Configure Power Automate cloud flows and Copilot Studio workflows | Major |
|  | Build Microsoft Foundry agents by using code that integrates with Microsoft Power Platform | New |
| **Develop Integrations** | **Develop integrations** | No % change |
| Implement data synchronization with Dataverse | Implement synchronization for Dataverse data | Minor |
|  | Create custom connectors | Minor |
