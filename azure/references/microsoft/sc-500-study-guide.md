# Study guide for Exam SC-500: Implementing End-to-End Security Controls for Cloud and AI Workloads

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/sc-500
Retrieved: 2026-11-23

## Purpose of this document

This study guide should help you understand what to expect on the exam and includes a summary of the topics the exam might cover and links to additional resources. The information and materials in this document should help you focus your studies as you prepare for the exam.

| Useful links | Description |
|---|---|
| [Your Microsoft Learn profile](https://learn.microsoft.com/en-us/users/) | Connecting your certification profile to Microsoft Learn allows you to schedule and renew exams and share and print certificates. |
| [Exam scoring and score reports](https://learn.microsoft.com/en-us/credentials/certifications/exam-scoring-reports) | A score of 700 or greater is required to pass. |
| [Exam sandbox](https://aka.ms/examdemo) | You can explore the exam environment by visiting our exam sandbox. |
| [Request accommodations](https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations) | If you use assistive devices, require extra time, or need modification to any part of the exam experience, you can request an accommodation. |

## About the exam

#### Languages

Some exams are localized into other languages. You can find these in the **Schedule Exam** section of the **Exam Details** webpage. If the exam isn’t available in your preferred language, you can request an additional 30 minutes to complete the exam.

The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured

### Audience profile

As a candidate for this Microsoft Certification, you’re a security engineer who protects organizational systems and data across cloud and hybrid environments by implementing comprehensive security controls that proactively help prevent unauthorized access and mitigate risks. Your role spans multiple security domains, including identity, network, application, data, and compute. You also help ensure that platforms, data, identities, and infrastructure used by AI workloads are securely implemented and monitored.

In this role, your responsibilities include:

- Securing access to resources by using Microsoft Entra ID and Azure Key Vault.
- Enforcing security and regulatory compliance.
- Securing storage, databases, and networking.
- Securing compute.
- Securing AI solutions.
- Managing and monitoring security posture.

You work closely with architects, administrators, engineers, analysts, and developers responsible for Azure, Microsoft 365, identity and access, information protection, security operations, DevOps, application development, database platforms, and networks.

For this exam, you should have practical experience in administration of Azure and hybrid environments, including compute, network, and storage. You need strong familiarity with Microsoft Entra ID and familiarity with Microsoft 365 administration.

### Skills at a glance

- Manage identity, access, and governance (20–25%)
- Secure storage, databases, and networking (25–30%)
- Secure compute (20–25%)
- Manage and monitor security posture (20–25%)

### Manage identity, access, and governance (20–25%)

#### Secure access to resources by using Microsoft Entra ID

- Implement and configure Privileged Identity Management (PIM)
- Implement conditional access policies
- Implement and configure authentication methods, including multifactor authentication (MFA) and passwordless
- Implement and configure identity for applications, including enterprise applications and app registrations
- Manage OAuth permission grants and consent settings
- Implement and configure managed identities for Azure resources

#### Secure secrets and keys by using Azure Key Vault

- Deploy Key Vault
- Configure Key Vault settings
- Configure access to Key Vault
- Configure firewall settings on Key Vault
- Manage keys, secrets, and certificates
- Scan for secrets by using Defender Cloud Security Posture Management (Defender CSPM)
- Implement Defender for Key Vault

#### Implement governance to enforce security and regulatory compliance

- Implement and configure security controls by using Azure Policy, including built-in and custom policy definitions
- Evaluate regulatory compliance by using Microsoft Defender for Cloud
- Implement and configure security controls in Defender for Cloud, including security standards and recommendations
- Implement resource locks
- Manage Azure built-in role assignments
- Manage custom roles, including Azure roles and Microsoft Entra roles
- Evaluate and remediate overprivileged access assignments by using Azure role-based access control (RBAC)
- Configure security controls for backup protection by using Azure Backup security features
- Implement and configure security controls by using infrastructure as code

### Secure storage, databases, and networking (25–30%)

#### Implement security for storage accounts

- Implement and configure security for storage accounts
- Configure Azure Storage firewall rules
- Implement Defender for Storage threat protection configurations
- Manage access to storage, including access policies

#### Implement security for databases

- Implement platform-level security configurations in Azure SQL
- Configure database auditing for Azure SQL Database and Azure SQL Managed Instance
- Configure Defender for Databases protection across Azure database services

#### Implement security for Azure network services

- Implement and manage network security groups (NSGs) and application security groups (ASGs)
- Implement and configure network access policies by using Azure Virtual Network Manager
- Configure security for an Azure Virtual WAN
- Implement and configure security for virtual private network (VPN) connections
- Implement and configure Microsoft Entra Private Access
- Configure Azure private endpoints to secure access to Azure platform as a service (PaaS) resources
- Configure Azure Private Link services to secure access to network resources
- Implement and configure Azure Firewall
- Evaluate effective security rules by using Azure Network Watcher diagnostics

### Secure compute (20–25%)

#### Implement security for AI

- Identify overexposure of data in SharePoint
- Identify risks related to Microsoft Copilot and AI apps by using Microsoft Purview Data Security Posture Management (DSPM)
- Enable and configure real-time protection for Microsoft Copilot Studio agents
- Implement conditional access for Microsoft Entra Agent ID
- Analyze blast radius for security risks related to Entra Agent ID by using Defender XDR
- Manage Entra Agent ID access
- Configure and deploy AI Gateway in Azure API Management for Microsoft Foundry
- Enable Defender for AI Service in Cloud Workload Protection in Defender for Cloud
- Configure guardrails for agent security in Foundry
- Monitor AI security by using the Data and AI security dashboard in Defender for Cloud
- Manage agents in Microsoft 365 admin center

#### Implement security for servers and virtual machines (VMs)

- Implement and configure disk encryption
- Plan and implement Azure Bastion
- Enable and enforce use of just-in-time (JIT) VM access
- Extend security controls to hybrid and multicloud servers by using Azure Arc
- Onboard servers to Defender for Servers in Defender for Cloud, including hybrid and multicloud scenarios
- Configure Defender for Servers settings, including vulnerability scanning, and endpoint detection and response (EDR)
- Implement and manage agentless scanning for VMs in Defender for Servers
- Configure security features on a VM, including secure boot, virtual Trusted Platform Module (vTPM), integrity monitoring, and security type
- Enforce security configuration of Azure-managed servers by using Azure Machine Configuration

#### Implement security for application platform services

- Detect misconfigurations and runtime risks in container workloads by using Defender for Containers
- Implement and configure security controls for Azure Kubernetes Service (AKS)
- Implement and configure security controls for Azure Container Registry
- Implement and configure security controls for Azure Container Instances and Azure Container Apps
- Implement and configure security controls for Azure Functions, including authentication and network access
- Implement and configure security controls for Azure Logic Apps
- Implement and configure security controls for Azure App Service
- Implement and configure Azure Web Application Firewall
- Implement security policies for back-end API protection by using API Management

### Manage and monitor security posture (20–25%)

#### Manage security posture by using Defender for Cloud

- Identify security risks by using Defender CSPM
- Evaluate compliance against security frameworks by using Defender for Cloud
- Enable and configure Defender for Cloud workload protection plans
- Connect hybrid cloud and multicloud environments to Defender for Cloud, including Amazon Web Services (AWS) and Google Cloud Platform (GCP)
- Configure Microsoft Defender Vulnerability Management settings for Azure VMs
- Discover unprotected assets and vulnerabilities by using Microsoft Defender External Attack Surface Management (EASM)

#### Implement activity and event collection in Microsoft Sentinel

- Create and connect workspaces in Microsoft Sentinel
- Assign roles in Microsoft Sentinel
- Implement and use content hub solutions
- Configure and use Microsoft data connectors for Azure resources
- Implement and configure syslog and Common Event Format (CEF) event collections
- Implement and configure collection of Windows Security events by using data collection rules, including Windows Event Forwarding (WEF)
- Create custom log tables in the workspace to store ingested data
- Implement automation rules and playbooks in Microsoft Sentinel
- Implement data retention in Microsoft Sentinel data stores
- Query Microsoft Purview Audit in Defender XDR

#### Implement Microsoft Security Copilot

- Configure workspaces for Security Copilot
- Manage permissions and roles in Security Copilot
- Enable and configure plugins
- Enable and configure Microsoft agents and Security Store agents

## Study resources

We recommend that you train and get hands-on experience before you take the exam. We offer self-study options and classroom training as well as links to documentation, community sites, and videos.

| Study resources | Links to learning and documentation |
|---|---|
| Get trained | [Choose from self-paced learning paths and modules or take an instructor-led course](https://learn.microsoft.com/en-us/credentials/certifications/cloud-and-ai-security-engineer-associate) |
| Find documentation | [Azure documentation](https://learn.microsoft.com/en-us/azure/?product=featured)[Microsoft Entra ID](https://learn.microsoft.com/en-us/azure/active-directory/)[Azure Firewall documentation](https://learn.microsoft.com/en-us/azure/firewall/)[Azure Firewall Manager documentation](https://learn.microsoft.com/en-us/azure/firewall-manager/)[Azure Application Gateway documentation](https://learn.microsoft.com/en-us/azure/application-gateway/)[Azure Front Door and CDN Documentation](https://learn.microsoft.com/en-us/azure/frontdoor/)[Web Application Firewall documentation](https://learn.microsoft.com/en-us/azure/web-application-firewall/)[Azure Key Vault documentation](https://learn.microsoft.com/en-us/azure/key-vault/)[Virtual network service endpoint policies for Azure Storage](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-service-endpoint-policies-overview)[Manage Azure Private Endpoints - Azure Private Link](https://learn.microsoft.com/en-us/azure/private-link/manage-private-endpoint?tabs=manage-private-link-powershell)[Create a Private Link service by using the Azure portal](https://learn.microsoft.com/en-us/azure/private-link/create-private-link-service-portal)[Azure DDoS Protection documentation](https://learn.microsoft.com/en-us/azure/ddos-protection/)[Virtual machines in Azure](https://learn.microsoft.com/en-us/azure/virtual-machines/overview)[Secure and use policies on virtual machines in Azure](https://learn.microsoft.com/en-us/azure/virtual-machines/security-policy)[Security - Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/overview-security)[Azure Policy documentation](https://learn.microsoft.com/en-us/azure/governance/policy/)[Plan your Defender for Servers deployment](https://learn.microsoft.com/en-us/azure/defender-for-cloud/defender-for-servers-introduction)[Microsoft Defender for Cloud documentation](https://learn.microsoft.com/en-us/azure/defender-for-cloud/)[Microsoft Threat Modeling Tool overview](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool)[Azure Monitor documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/)[Microsoft Sentinel documentation](https://learn.microsoft.com/en-us/azure/sentinel/)[Azure Storage documentation](https://learn.microsoft.com/en-us/azure/storage/)[Azure Files documentation](https://learn.microsoft.com/en-us/azure/storage/files/)[Azure SQL documentation](https://learn.microsoft.com/en-us/azure/azure-sql/?view=azuresql) |
| Ask a question | [Microsoft Q&A \| Microsoft Docs](https://learn.microsoft.com/en-us/answers/products/) |
| Get community support | [Azure Community Support](https://azure.microsoft.com/support/community/) |
| Follow Microsoft Learn | [Microsoft Learn - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/microsoft-learn/ct-p/MicrosoftLearn) |
| Find a video | [Exam Readiness Zone](https://learn.microsoft.com/en-us/shows/exam-readiness-zone/?terms=AZ-500)[Azure Fridays](https://azure.microsoft.com/resources/videos/azure-friday/)[Browse other Microsoft Learn shows](https://learn.microsoft.com/en-us/shows/browse) |
