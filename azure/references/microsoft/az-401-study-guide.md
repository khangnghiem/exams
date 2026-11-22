# Study guide for Exam AZ-401: Designing and Implementing Microsoft Agentic DevOps Solutions

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-401
Retrieved: 2026-11-23

## Purpose of this document

This study guide should help you understand what to expect on the exam and includes a summary of the topics the exam might cover and links to additional resources. The information and materials in this document should help you focus your studies as you prepare for the exam.

| Useful links | Description |
|---|---|
| [Certification renewal](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification) | Microsoft associate, expert, and specialty certifications expire annually. You can renew by passing a **free** online assessment on Microsoft Learn. |
| [Your Microsoft Learn profile](https://learn.microsoft.com/en-us/users/) | Connecting your certification profile to Microsoft Learn allows you to schedule and renew exams and share and print certificates. |
| [Exam scoring and score reports](https://learn.microsoft.com/en-us/credentials/certifications/exam-scoring-reports) | A score of 700 or greater is required to pass. |
| [Exam sandbox](https://aka.ms/examdemo) | You can explore the exam environment by visiting our exam sandbox. |
| [Request accommodations](https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations) | If you use assistive devices, require extra time, or need modification to any part of the exam experience, you can request an accommodation. |

## Updates to the exam

Our exams are updated periodically to reflect skills that are required to perform a role. We have included two versions of the Skills Measured objectives depending on when you are taking the exam.

We always update the English language version of the exam first. Some exams are localized into other languages, and those are updated approximately eight weeks after the English version is updated. While Microsoft makes every effort to update localized versions of exams as noted, there may be times when localized versions of an exam are not updated on this schedule. Other available languages are listed in the **Schedule Exam** section of the **Exam Details** webpage. If the exam isn't available in your preferred language, you can request an additional 30 minutes to complete the exam.

The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured

### Audience profile

As a Microsoft agentic DevOps engineer, you’re a developer or infrastructure administrator who also has subject matter expertise in working with people, processes, and products to enable continuous delivery of value to organizations. You enhance DevOps processes by integrating AI assistance tools.

Your responsibilities for this role include delivering Microsoft DevOps solutions that provide continuous security, integration, testing, delivery, deployment, monitoring, reliability, and feedback. You design flow of work, collaboration, communication, source control, automation and implement the solution by using AI assistance.

As an agentic DevOps engineer, you collaborate with other roles including:

- Developers
- Site reliability engineers
- Platform engineers
- Azure administrator
- Security engineers

You must have strong skills in either administering or developing solutions using Microsoft technologies. You should have practical experience with code languages used in DevOps, including YAML, KQL, and Bicep. You should also have experience implementing both Azure DevOps and GitHub solutions using Microsoft and GitHub AI tools.

### Skills at a glance

- Design and implement processes and communications (15–20%)
- Design and implement a source control strategy (10–15%)
- Design and implement build and release pipelines (35–40%)
- Design and implement a security and compliance plan (15–20%)
- Implement an instrumentation strategy (15–20%)

### Design and implement processes and communications (15–20%)

#### Design traceability and flow of work

- Design a structure for the flow of work, including plan, build, deploy, and operate phases
- Design a strategy for feedback cycles, including notifications
- Design a strategy for tracking work using Azure Boards
- Design traceability, including repositories, bugs, and quality

#### Design and implement success metrics for DevOps

- Translate business KPIs into success metrics and standards for project planning, development, testing, delivery, operations, and security
- Implement queries to evaluate success metrics for DevOps by using AI-assisted tools

#### Configure collaboration and communication

- Document a project, including wikis, readmes, change logs, releases, licenses, code owners, and process diagrams, by using AI-assisted tools
- Specify requirements and restrictions for agentic development, including agents, skills, and loops
- Configure MCP servers, including Azure DevOps MCP server and GitHub MCP server
- Configure integration by using webhooks, MCP servers, and skills
- Configure integration between Azure Boards and GitHub repositories by using MCP

### Design and implement a source control strategy (10–15%)

#### Design and implement branching strategies for Azure DevOps and GitHub

- Design a branch strategy, including trunk-based, feature branch, release branch, Git Worktree, Git flow, and GitHub flow
- Design and implement pull request workflows by using branch policies and branch protection rules
- Implement branch merging restrictions by using branch policies and branch protection rules
- Implement branch policies and branch protection rules for GitHub Copilot

#### Configure and manage repositories for Azure DevOps and GitHub

- Configure permissions
- Configure tags
- Implement traceability in repositories, including code quality, code coverage, and deep links to the work item or issue
- Create and configure Git hooks that automatically check code
- Perform a repository-to-repository migration from Azure DevOps to GitHub
- Recover or remove specific data by using Git commands

### Design and implement build and release pipelines (35–40%)

#### Design and implement a package management strategy

- Recommend package management tools including Azure Artifacts and GitHub Packages
- Design and implement package feeds and views for local and upstream sources
- Design and implement a dependency versioning strategy for code assets and packages, including semantic versioning (SemVer) and date-based (CalVer)
- Design and implement a versioning strategy for pipeline artifacts

#### Design and implement a testing strategy for Azure DevOps pipelines and GitHub Actions

- Design quality and release gates
- Implement quality and release gates by using GitHub Copilot and MCP servers
- Design a comprehensive testing strategy, including local tests, unit tests, integration tests, and load tests
- Implement tests in a pipeline, including configuring test tasks, configuring test agents, and documenting test results, by using GitHub Copilot and MCP servers
- Implement code coverage analysis by using GitHub Copilot and MCP servers

#### Design and implement Azure DevOps pipelines and GitHub Actions

- Select a deployment automation solution, including Azure Pipelines and GitHub Actions
- Design an Azure DevOps agent or GitHub runner infrastructure, including cost, tool selection, licenses, connectivity, and maintainability
- Implement an Azure DevOps or GitHub runner agent infrastructure
- Design and implement integration between Azure Pipelines and GitHub repositories
- Develop pipelines in YAML by using GitHub Copilot
- Develop and implement pipeline trigger rules
- Design and implement a strategy for job execution order, including parallelism and multi-stage pipelines
- Create reusable pipeline elements, including YAML templates, task groups, variables, and variable groups
- Design and implement checks and approvals by using YAML-based environments
- Design and implement GitHub Agentic Workflows

#### Design and implement deployments

- Design a deployment strategy, including blue-green, canary, ring, progressive exposure, feature flags, and A/B testing
- Design a pipeline to ensure that dependency deployments are reliably ordered
- Plan for minimizing downtime during deployments by using load balancing, deployment slot usage and swap, and rolling deployments
- Design a hotfix path plan for responding to high-priority code fixes
- Design and implement a resiliency strategy for deployment
- Implement deployment by using containers, binaries, scripts, and database tasks

#### Design and implement infrastructure as code (IaC)

- Recommend a strategy for IaC and configuration management
- Implement a configuration management strategy for application infrastructure

#### Maintain Azure DevOps pipelines and GitHub Actions

- Monitor pipeline health, including failure rate, duration, and flaky tests
- Optimize a pipeline for cost, time, performance, and reliability
- Design and implement a retention strategy for pipeline artifacts and dependencies

### Design and implement a security and compliance plan (15–20%)

#### Design and implement authentication and authorization methods

- Choose between Microsoft Entra service principals and managed identities for Azure resources
- Implement and manage GitHub authentication, including GitHub Apps, GITHUB_TOKEN, and personal access tokens
- Implement and manage secretless authentication in Azure Pipelines and GitHub Actions
- Implement and manage Azure DevOps service connections and personal access tokens
- Design and implement permissions and access levels in Azure DevOps and GitHub
- Configure projects in Azure DevOps (ADO) and GitHub, including ADO teams

#### Design and implement a strategy for managing sensitive information in automation

- Integrate Azure Key Vault into Azure Pipelines and GitHub Actions
- Implement and manage secrets, keys, and certificates
- Design and implement a strategy for managing sensitive information during deployment, including Azure Pipelines secure files and GitHub secrets
- Design Azure Pipelines and GitHub Actions to prevent leakage of sensitive information

#### Automate security and compliance scanning

- Design a strategy for security, vulnerability, and compliance scanning
- Configure dependency scanning, code scanning, and secret scanning by using GitHub Advanced Security for Azure DevOps and GitHub Advanced Security
- Connect Microsoft Defender for Cloud DevOps Security to other DevOps environments, including Azure DevOps and GitHub

### Implement an instrumentation strategy (15–20%)

#### Configure monitoring for Azure DevOps and GitHub platforms

- Design dashboards, including flow of work, cycle time, time to recovery, and lead time
- Configure Azure Monitor and Log Analytics to integrate with Azure DevOps and GitHub
- Configure monitoring in GitHub, including enabling GitHub insights and creating and configuring charts
- Configure alerts for events in Azure Pipelines and GitHub Actions

#### Monitor Azure workloads by using AI agents

- Deploy and configure Azure Copilot Observability Agent
- Deploy and configure Azure SRE Agent
- Investigate and resolve issues raised by Azure SRE Agent

#### Analyze metrics from instrumentation by using AI agents

- Analyze infrastructure performance indicators, including CPU, memory, disk, and network
- Analyze application performance by using telemetry and instrumentation data
- Analyze distributed tracing by using Azure Monitor Application Insights
- Configure and collection and management GitHub Copilot agent logs
- Interrogate logs by using natural language queries or basic Kusto Query Language (KQL) queries

## Study resources

We recommend that you train and get hands-on experience before you take the exam. We offer self-study options and classroom training as well as links to documentation, community sites, and videos.

| Study resources | Links to learning and documentation |
|---|---|
| Get trained | [Choose from self-paced learning paths and modules or take an instructor-led course](https://learn.microsoft.com/en-us/credentials/certifications/exams/az-401#two-ways-to-prepare) |
| Find documentation | [DevOps resource center](https://learn.microsoft.com/en-us/devops/)[Azure DevOps documentation](https://learn.microsoft.com/en-us/azure/devops/?view=azure-devops)[Azure Boards](https://learn.microsoft.com/en-us/azure/devops/boards/)[Azure Key Vault Keys, Secrets, and Certificates Overview](https://learn.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates)[Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/)[Azure Pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/)[Azure Repos](https://learn.microsoft.com/en-us/azure/devops/repos/)[Work with Azure DevOps and GitHub](https://learn.microsoft.com/en-us/azure/developer/github/integrate-azure-devops)[Authenticating with a GitHub App](https://docs.github.com/apps/creating-github-apps/authenticating-with-a-github-app)[Configure GitHub Advanced Security for Azure DevOps](https://learn.microsoft.com/en-us/azure/devops/repos/security/configure-github-advanced-security-features?view=azure-devops&pivots=standalone-ghazdo)[GitHub Actions](https://docs.github.com/actions)[GitHub Advanced Security](https://docs.github.com/get-started/learning-about-github/about-github-advanced-security)[GitHub Copilot](https://docs.github.com/copilot) |
| Ask a question | [Microsoft Q&A \| Microsoft Docs](https://learn.microsoft.com/en-us/answers/products/) |
| Get community support | [Azure DevOps - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/azure-devops/bd-p/AzureDevOpsForum) |
| Follow Microsoft Learn | [Microsoft Learn - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/microsoft-learn/ct-p/MicrosoftLearn) |
| Find a video | [Exam Readiness Zone](https://learn.microsoft.com/en-us/shows/exam-readiness-zone/)[Microsoft Learn Shows](https://learn.microsoft.com/en-us/shows/browse) |
