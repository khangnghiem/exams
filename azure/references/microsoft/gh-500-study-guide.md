# Study guide for Exam GH-500: GitHub Advanced Security

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/gh-500
Retrieved: 2026-11-23

## Purpose of this document

This study guide should help you understand what to expect on the exam and includes a summary of the topics the exam might cover and links to additional resources. The information and materials in this document should help you focus your studies as you prepare for the exam.

| Useful links | Description |
|---|---|
| [Certification renewal](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification) | Microsoft associate, expert, and specialty certifications expire annually. You can renew by passing a free online assessment on Microsoft Learn. |
| [Your Microsoft Learn profile](https://learn.microsoft.com/en-us/users) | Connecting your certification profile to Microsoft Learn allows you to schedule and renew exams and share and print certificates. |
| [Exam scoring and score reports](https://learn.microsoft.com/en-us/credentials/certifications/exam-scoring-reports) | A score of 700 or greater is required to pass. |
| [Exam sandbox](https://aka.ms/examdemo) | You can explore the exam environment by visiting our exam sandbox. |
| [Request accommodations](https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations) | If you use assistive devices, require extra time, or need modification to any part of the exam experience, you can request an accommodation. |

## About the exam

Some exams are localized into other languages, and those are updated approximately eight weeks after the English version is updated. While Microsoft makes every effort to update localized versions as noted, there may be times when the localized versions of an exam are not updated on this schedule. Other available languages are listed in the **Schedule Exam** section of the **Exam Details** webpage. If the exam isn't available in your preferred language, you can request an additional 30 minutes to complete the exam.

The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured as of July 2026

### Audience profile

Candidates for this exam have experience using GitHub Advanced Security (GHAS) to secure code, secrets, and dependencies across the software development lifecycle. They can configure security features, triage and remediate alerts, and apply prevention-first practices using policies, workflows, and automation. Candidates are familiar with GitHub fundamentals, CI/CD, and secure development concepts.

### Skills at a glance

- Describe GitHub Security suites, features, and ecosystem (15–20%)
- Configure and use Secret Protection (formerly secret scanning) (15–20%)
- Configure and use supply chain security (formerly Dependabot/Dependency Review) (15–20%)
- Configure and use Code Security (formerly Code Scanning with CodeQL) (10–15%)
- Security operations: best practices, prioritization, and remediation (15–20%)
- GitHub Security suites administration (10–15%)

### Describe GitHub Security suites, features, and ecosystem (15–20%)

#### Understand GitHub Security suites and architecture

- Describe GitHub Security suite structure and navigation
- Contrast Code Security, Secret Protection, and Supply Chain Security
- Differentiate security feature availability for public repositories vs. enterprise environments
- Explain features and benefits of the Security Overview

#### Apply secure SDLC and security strategies

- Explain differences and interplay between Secret Protection and Code Security
- Describe end-to-end secure SDLC using GitHub Security suites
- Compare prevention-first approaches vs. gate-based security strategies
- Explain security campaigns and their role in reducing risk

#### Detect, manage, and respond to security alerts

- Identify vulnerability and secret detection mechanisms
- Choose and act on security alerts (alert management, policies, workflows)
- Explain implications and best practices for ignoring or dismissing alerts
- Describe developer, security, and admin responsibilities for alerts and remediation

#### Manage access, governance, and supply chain security

- Explain alert access management, roles, delegated bypass, and enforcement
- Describe supply chain security concepts and alert information across the SDLC

### Configure and use Secret Protection (formerly secret scanning) (15–20%)

#### Enable and configure Secret Protection

- Enable GitHub Secret Protection at the repository and organization levels
- Configure Secret Protection settings and feature availability
- Contrast Secret Protection behavior for public vs. private/enterprise repositories

#### Prevent secret exposure

- Explain Push Protection and how it prevents secrets at the source
- Describe validity checks and prioritized alerting for high-confidence secrets

## Manage and respond to Secret Protection alerts

- Describe the Secret Protection alert lifecycle (creation, status, dismissal)
- Respond to secret alerts and apply appropriate remediation actions
- Explain implications and best practices for dismissing or ignoring alerts

#### Control access, policies, and customization

- Explain role-based and delegated bypass policies in Secret Protection
- Configure alert recipients and exclusions
- Create and manage custom secret patterns

### Configure and use supply chain security (formerly Dependabot/Dependency Review) (15–20%)

#### Understand and manage dependency and supply chain risks

- Comprehensive dependency security (tools, vulnerability databases, SBOMs)
- Generate and interpret the dependency graph
- SBOM usage: export options, formats, and supply chain context

#### Detect, prioritize, and respond to supply chain alerts

- Supply chain alerts and security updates (prioritization, EPSS scoring)
- Remediating supply chain alerts through campaigns and pull requests
- Auto-dismiss behavior and security campaign configuration

#### Secure dependencies during development

- Dependency Review (pre-merge checks, license and compliance validation, configuration)
- Advanced dependency update rules (grouping, auto-dismiss, update strategies)

#### Configure policies, permissions, and integrations

- Permissions and role-based alert assignment
- Workflow management for dependency and supply chain security
- External notifications, webhooks, and security integrations

### Configure and use Code Security (formerly Code Scanning with CodeQL) (10–15%)

#### Understand code scanning approaches and tooling

- Native and third-party code scanning options
- Choosing between CodeQL and third-party analysis tools
- SARIF file ingestion, management, and interoperability

#### Set up and configure Code Security

- Enable code security using GitHub Actions or external CI systems
- Configure code scanning workflows and workflow templates
- Use matrix builds and define appropriate scan frequency

#### Analyze, triage, and remediate code scanning results

- Review scan results, including dataflow analysis insights
- Alert lifecycles, autofix capabilities, and remediation workflows
- Dismissing alerts and managing severity and category classifications

#### Optimize and automate Code Security operations

- Advanced configuration and customization
- Troubleshooting scan failures and performance issues

### Security operations: best practices, prioritization, and remediation (15–20%)

#### Understand vulnerability context and remediation frameworks

- CVE, CWE, and GitHub Security Advisory concepts
- End-to-end remediation workflows across security alerts and advisories

#### Prioritize and manage security work at scale

- Defining, prioritizing, and enforcing severity and remediation rulesets
- Campaign-based remediation strategies and bulk alert management
- Automated alert dismissal and documentation practices

#### Customize and optimize security detection

- Customizing CodeQL query suites and language-specific analysis
- Tailoring security detection to organizational risk profiles

#### Collaborate across roles and enforce governance

- Security roles, delegated exceptions, and alert ownership
- Collaboration on alerts and security campaigns across teams
- Cross-suite rulesets, policies, and enforcement mechanisms

#### Shift left and strengthen preventive security

- Early vulnerability prevention through push protection, dependency scanning, and pre-merge analysis

### GitHub Security suites administration (10–15%)

#### Roll out and manage security features at scale

- Enable GitHub Security Suites at enterprise, organization, and repository levels
- Understand feature availability and differences across GitHub Enterprise Cloud and GitHub Enterprise Server

#### Configure security features and defaults

- Enable Code Security (CodeQL), Secret Protection, and Supply Chain Security
- Define default configurations and inheritance behavior

#### Define governance, access, and Code Security workflows

- Define enterprise and organization security policies and rulesets
- Configure enforcement boundaries, bypass permissions, and exceptions
- Define administrator, security manager, and developer roles
- Configure permissions for managing and dismissing security alerts
- Enable and configure default or approved custom CodeQL workflows
- Understand APIs and automation methods for large-scale security configuration and governance

#### Manage CodeQL and security automation

- Enable and configure default or approved custom CodeQL workflows
- Understand available APIs and automation methods for large-scale security configuration and governance

## Study resources

We recommend that you train and get hands-on experience before you take the exam. We offer self-study options and classroom training as well as links to documentation, community sites, and videos.

| Study resources | Links to learning and documentation |
|---|---|
| Get trained | Choose from self-paced learning paths and modules or take an instructor-led course on Microsoft Learn – [GitHub Advanced Security Part 1](https://learn.microsoft.com/en-us/training/paths/github-advanced-security/) and [GitHub Advanced Security Part 2](https://learn.microsoft.com/en-us/training/paths/github-advanced-security-2/) |
| Find documentation | [Describe the GHAS security features and functionality](https://docs.github.com/get-started/learning-about-github/about-github-advanced-security)[Configure and use secret scanning](https://docs.github.com/code-security/secret-scanning)[Configure and use Dependabot](https://docs.github.com/code-security/getting-started/dependabot-quickstart-guide) and [Dependency Review](https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review)[Configure and use Code Scanning with CodeQL](https://docs.github.com/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning)[Describe GitHub Advanced Security best practices, results, and how to take corrective measures](https://learn.microsoft.com/en-us/training/modules/introduction-github-advanced-security/) |
| Ask a question | [GitHub Community Discussions](https://github.community/) |
| Get community support | [GitHub Blog](https://github.blog/) |
| Follow GitHub | [Twitter](https://twitter.com/github)[LinkedIn](https://www.linkedin.com/company/github)[Instagram](https://www.instagram.com/github/) |
| Find a video | [YouTube](https://www.youtube.com/github) |

## Change log

This exam has changed significantly (e.g., new objectives were added, some were removed, existing objectives may have moved to different functional groups, and all were reworded) on July, 2026.
