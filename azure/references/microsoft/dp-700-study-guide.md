# Study Guide for Exam DP-700: Implementing Data Engineering Solutions Using Microsoft Fabric

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700
Retrieved: 2026-06-20

## Purpose of this document

This study guide should help you understand what to expect on the exam and includes a summary of the topics the exam might cover and links to additional resources. The information and materials in this document should help you focus your studies as you prepare for the exam.

## Useful links

| Description | Link |
|---|---|
| How to earn the certification | https://learn.microsoft.com/en-us/credentials/certifications/fabric-data-engineering-associate/ |
| Certification renewal | https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification |
| Your Microsoft Learn profile | https://learn.microsoft.com/en-us/users |
| Exam scoring and score reports | https://learn.microsoft.com/en-us/credentials/certifications/exam-scoring-reports |
| Exam sandbox | https://aka.ms/examdemo |
| Request accommodations | https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations |
| Take a free Practice Assessment | https://learn.microsoft.com/en-us/credentials/certifications/azure-administrator/practice/assessment?assessment-type=practice&assessmentId=1704375541 |

## About the exam

### Languages

Some exams are localized into other languages, and those are updated approximately eight weeks after the English version is updated. If the exam isn't available in your preferred language, you can request an additional 30 minutes to complete the exam.

> **Note:** The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

> **Note:** Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured as of April 20, 2026

### Audience profile

As a candidate for this exam, you should have subject matter expertise with data loading patterns, data architectures, and orchestration processes. Your responsibilities for this role include:

- Ingesting and transforming data.
- Securing and managing an analytics solution.
- Monitoring and optimizing an analytics solution.

You work closely with analytics engineers, architects, analysts, and administrators to design and deploy data engineering solutions for analytics.

You should be skilled at manipulating and transforming data by using Structured Query Language (SQL), PySpark, and Kusto Query Language (KQL).

### Skills at a glance

- Implement and manage an analytics solution (30–35%)
- Ingest and transform data (30–35%)
- Monitor and optimize an analytics solution (30–35%)

### Implement and manage an analytics solution (30–35%)

#### Configure Microsoft Fabric workspace settings

- Configure Spark workspace settings
- Configure domain workspace settings
- Configure OneLake workspace settings
- Configure Dataflows Gen2 workspace settings

#### Implement lifecycle management in Fabric

- Configure version control
- Implement database projects
- Create and configure deployment pipelines

#### Configure security and governance

- Implement workspace-level access controls
- Implement item-level access controls
- Implement row-level, column-level, object-level, and folder/file-level access controls
- Implement dynamic data masking
- Apply sensitivity labels to items
- Endorse items
- Implement and use Microsoft Fabric audit logs
- Configure and implement OneLake security

#### Orchestrate processes

- Choose between Dataflow gen 2, a pipeline and a notebook
- Design and implement schedules and event-based triggers
- Implement orchestration patterns with notebooks and pipelines, including parameters and dynamic expressions

### Ingest and transform data (30–35%)

#### Design and implement loading patterns

- Design and implement full and incremental data loads
- Prepare data for loading into a dimensional model
- Design and implement a loading pattern for streaming data

#### Ingest and transform batch data

- Choose an appropriate data store
- Choose between Dataflows Gen2, notebooks, KQL, and T-SQL for data transformation
- Create and manage OneLake shortcuts
- Implement mirroring
- Ingest data by using pipelines
- Transform data by using PySpark, SQL, and KQL
- Denormalize data
- Group and aggregate data
- Handle duplicate, missing, and late-arriving data

#### Ingest and transform streaming data

- Choose an appropriate streaming engine
- Choose between native tables and OneLake shortcuts in Real-Time Intelligence
- Choose between Query acceleration for OneLake shortcuts and standard OneLake shortcuts in Real-Time Intelligence
- Process data by using Eventstreams
- Process data by using Spark structured streaming
- Process data by using KQL
- Create windowing functions

### Monitor and optimize an analytics solution (30–35%)

#### Monitor Fabric items

- Monitor data ingestion
- Monitor data transformation
- Monitor semantic model refresh
- Configure alerts

#### Identify and resolve errors

- Identify and resolve pipeline errors
- Identify and resolve Dataflow Gen2 errors
- Identify and resolve notebook errors
- Identify and resolve Eventhouse errors
- Identify and resolve Eventstream errors
- Identify and resolve T-SQL errors
- Identify and resolve OneLake shortcut errors

#### Optimize performance

- Optimize a Lakehouse table
- Optimize a pipeline
- Optimize a data warehouse
- Optimize Eventstreams and Eventhouses
- Optimize Spark performance
- Optimize query performance

## Study resources

We recommend that you train and get hands-on experience before you take the exam.

- **Get trained:** Choose from self-paced learning paths and modules or take an instructor-led course
- **Find documentation:**
  - [Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/)
  - [What is Data engineering in Microsoft Fabric?](https://learn.microsoft.com/en-us/fabric/data-engineering/data-engineering-overview)
- **Ask a question:** [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/products/)
- **Get community support:** [Analytics on Azure - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/analytics-on-azure/bd-p/AnalyticsonAzureDiscussion)
- **Follow Microsoft Learn:** [Microsoft Learn - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/microsoft-learn/ct-p/MicrosoftLearn)
- **Find a video:** [Exam Readiness Zone](https://learn.microsoft.com/en-us/shows/exam-readiness-zone/), [Data Exposed](https://learn.microsoft.com/en-us/shows/data-exposed/)

---

*Last updated on 2026-03-20 (source page).*
