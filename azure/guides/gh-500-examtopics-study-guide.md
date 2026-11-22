# GH-500 GitHub Advanced Security Study Guide

_25 questions generated from ExamTopics discussions._

**Official Exam & Registration:** [Register for GH-500 on Microsoft Learn](https://learn.microsoft.com/en-us/credentials/certifications/github-advanced-security/?practice-assessment-type=certification)

## Table of contents

- [Q1.1](#q1-1)
- [Q1.2](#q1-2)
- [Q2.1](#q2-1)
- [Q2.7](#q2-7)
- [Q2.8](#q2-8)
- [Q2.11](#q2-11)
- [Q2.13](#q2-13)
- [Q2.20](#q2-20)
- [Q2.23](#q2-23)
- [Q3.7](#q3-7)
- [Q3.11](#q3-11)
- [Q3.14](#q3-14)
- [Q3.15](#q3-15)
- [Q3.18](#q3-18)
- [Q3.24](#q3-24)
- [Q3.27](#q3-27)
- [Q3.28](#q3-28)
- [Q3.29](#q3-29)
- [Q3.33](#q3-33)
- [Q4.6](#q4-6)
- [Q4.10](#q4-10)
- [Q4.11](#q4-11)
- [Q4.32](#q4-32)
- [Q5.1](#q5-1)
- [Q5.3](#q5-3)

<a id="q1-1"></a>
## Q1.1 (ID 328094)

A secret scanning alert should be closed as “used in tests” when a secret is:

⭕ **A.** in a test file.
✅ **B.** solely used for tests.
⭕ **C.** in the readme.md file.
⭕ **D.** not a secret in the production environment.

**Correct answer:** B
**Most voted:** B

### Top explanations
- **K5000ism** (1 upvotes [Most Recent, Selected Answer: B]): Used in tests

<a id="q1-2"></a>
## Q1.2 (ID 313256)

What happens when you enable secret scanning on a private repository?

⭕ **A.** Repository administrators can view Dependabot alerts.
⭕ **B.** Dependency review, secret scanning, and code scanning are enabled.
⭕ **C.** Your team is subscribed to security alerts.
✅ **D.** GitHub performs a read-only analysis on the repository.

**Correct answer:** D
**Most voted:** D

### Top explanations
- **tdkc** (3 upvotes [Most Recent, Selected Answer: D]): A is Incorrect. Enabling secret scanning does not automatically enable Dependabot alerts (a separate feature for vulnerable dependencies). When you enable secret scanning on a private repository (which requires GitHub Advanced Security), several actions occur, one of them is an Immediate Historical Scan: GitHub immediately initiates a scan of the entire Git history across all branches in the repository for known secret patterns.
  Answer should be D. GitHub performs a read-only analysis on the repository.

<a id="q2-1"></a>
## Q2.1 (ID 315491)

What is the first step you should take to fix an alert in secret scanning?

✅ **A.** Remove the secret in a commit to the main branch.
⭕ **B.** Archive the repository.
⭕ **C.** Update your dependencies.
⭕ **D.** Revoke the alert if the secret is still valid.

**Correct answer:** A
**Most voted:** A

### Top explanations
- **ziggy1117** (2 upvotes [Most Recent, Selected Answer: A]): A. Remove the secret in a commit to the main branch.
  We first need to ensure the secret is no longer in the main branch.
  D is incorrect because we need to revoke the secret NOT revoke the alert

<a id="q2-7"></a>
## Q2.7 (ID 311865)

Which patterns are secret scanning validity checks available to?

⭕ **A.** high entropy strings
⭕ **B.** custom patterns
⭕ **C.** push protection patterns
✅ **D.** partner patterns

**Correct answer:** D
**Most voted:** D

### Top explanations
- **neophantom** (3 upvotes [Selected Answer: D]): D should be correct answer
- **dd6adc9** (1 upvotes [Most Recent, Selected Answer: D]): Secret scanning validity checks are only available for partner patterns (secrets from supported service providers that GitHub has integrations with).
  Why the others don’t apply:
  High entropy strings → generic detection, no validity checks
  Custom patterns → user-defined, no validity checks
  Push protection patterns → a protection feature, not a pattern type that gets validity checks

<a id="q2-8"></a>
## Q2.8 (ID 315147)

What role is required to change a repository’s code scanning severity threshold that fails a pull request status check?

⭕ **A.** Maintain
⭕ **B.** Write
✅ **C.** Admin
⭕ **D.** Triage

**Correct answer:** C
**Most voted:** C

### Top explanations
- **adelbar** (1 upvotes [Most Recent, Selected Answer: C]): Changing the code scanning severity threshold modifies repository security rules. "Write" access can manage alerts, but "Admin" access is required to change the threshold.
- **0547a52** (1 upvotes [Selected Answer: C]): Changing the code scanning severity threshold (which determines when a pull request fails) is a repository-level configuration. Only users with Admin permissions can modify these settings.

<a id="q2-11"></a>
## Q2.11 (ID 314631)

Which of the following features helps to prioritize secret scanning alerts that present an immediate risk?

⭕ **A.** non-provider patterns
⭕ **B.** push protection
✅ **C.** secret validation
⭕ **D.** custom pattern dry runs

**Correct answer:** C
**Most voted:** C

### Top explanations
- **tdkc** (2 upvotes [Selected Answer: C]): C Secret Validation. Validity checks help you prioritize alerts by automatically indicating if a detected secret is still active or inactive (invalidated) by communicating with the issuing service provider (for supported partner patterns). The reason validity checks are the correct feature to help prioritize existing secret scanning alerts (those already exposed in the history or present in the codebase) over push protection is based purely on their intended function.
- **0a9a335** (1 upvotes [Most Recent, Selected Answer: C]): Secret validation helps prioritize secret scanning alerts by checking whether a detected secret is still active (i.e., valid and in use). This allows teams to focus on alerts that present an immediate risk, as only active secrets can be exploited.

<a id="q2-13"></a>
## Q2.13 (ID 314630)

Which of the following statements most accurately describes push protection for secret scanning custom patterns?

⭕ **A.** Push protection is enabled by default for new custom patterns.
⭕ **B.** Push protection must be enabled for all, or none, of a repository’s custom patterns.
⭕ **C.** Push protection is not available for custom patterns.
✅ **D.** Push protection is an opt-in experience for each custom pattern.

**Correct answer:** D
**Most voted:** D

### Top explanations
- **tdkc** (3 upvotes [Most Recent, Selected Answer: D]): It cannot be B because it says ..., or none, ...
  The most accurate is D. To enable push protection for secret scanning custom patterns in GitHub Advanced Security (GHAS), you must first ensure that generic secret scanning and push protection are generally enabled for the repository, organization, or enterprise. Once the base features are enabled, push protection is an opt-in experience for each custom pattern.

<a id="q2-20"></a>
## Q2.20 (ID 315148)

By default, where will secret scanning look in a repository in order to execute its job? Each correct answer presents part of the solution. (Choose three.)

✅ **A.** all files in the repository
⭕ **B.** dependencies
⭕ **C.** selected files in the repository
✅ **D.** full commit history
✅ **E.** all branches

**Correct answer:** A, D, E
**Most voted:** ADE

### Top explanations
- **ziggy1117** (2 upvotes [Most Recent, Selected Answer: ADE]): A. all files in the repository
  D. full commit history
  E. all branches
  By default it will look at all files. You can specify which files or directories secret scanning should ignore (i.e., not scan) by creating a .github/secret_scanning.yml file in your repository with a paths-ignore setting. But its not the default way

<a id="q2-23"></a>
## Q2.23 (ID 315149)

Which of the following pre-defined roles is required to manage code scanning alerts in a repository?

✅ **A.** Maintain
⭕ **B.** View
⭕ **C.** Read
⭕ **D.** Triage

**Correct answer:** A
**Most voted:** A

### Top explanations
- **dd6adc9** (2 upvotes [Most Recent, Selected Answer: A]): While it might seem like "Triage" would be enough (since it sounds like a role for managing issues), GitHub’s permission structure for security features is a bit more specific.Permission BreakdownHere is how the roles differ regarding code scanning:
  Read / View Can see that alerts exist, but generally cannot dismiss or change their status.
  Triage: Can manage issues and pull requests, but does not have the elevated permissions required to manage security alerts.
  Maintain: Can manage most aspects of a repository, including managing code scanning alerts (dismissing, reopening, etc.).
  Admin: Has full control, including the ability to enable/disable code scanning and manage alerts.

<a id="q3-7"></a>
## Q3.7 (ID 315922)

If default code security settings have not been changed at the repository, organization, or enterprise level, which repositories receive Dependabot alerts?

⭕ **A.** private repositories
⭕ **B.** none
✅ **C.** repositories owned by an organization
⭕ **D.** repositories owned by an enterprise account

**Correct answer:** C
**Most voted:** C

### Top explanations
- **0a9a335** (1 upvotes [Most Recent, Selected Answer: C]): By default, if no changes have been made to the code security settings, Dependabot alerts are enabled for repositories owned by an organization. Private repositories and enterprise accounts do not receive Dependabot alerts by default unless explicitly configured.

<a id="q3-11"></a>
## Q3.11 (ID 315160)

Where can you find a deleted line of code that contained a secret value?

⭕ **A.** Issues
⭕ **B.** Dependency graph
✅ **C.** Commits
⭕ **D.** Insights

**Correct answer:** C
**Most voted:** C

### Top explanations
- **ivantsanev** (3 upvotes [Most Recent, Selected Answer: C]): I this should be C. Finding files changes can be easily seen in Commits tab.

<a id="q3-14"></a>
## Q3.14 (ID 316017)

Assuming that notification and alert recipients are not customized, what does GitHub do when it identifies a vulnerable dependency in a repository where Dependabot alerts are enabled? (Each answer presents part of the solution. Choose two.)

✅ **A.** It generates a Dependabot alert and displays it on the Security tab for the repository.
⭕ **B.** It consults with a security service and conducts a thorough vulnerability review.
⭕ **C.** It generates Dependabot alerts by default for all private repositories.
✅ **D.** It notifies the repository administrators about the new alert.

**Correct answer:** A, D
**Most voted:** AD

### Top explanations
- **0a9a335** (2 upvotes [Most Recent, Selected Answer: AD]): When GitHub identifies a vulnerable dependency in a repository where Dependabot alerts are enabled, it:
  Generates a Dependabot alert and displays it on the Security tab of the repository.
  Sends a notification to repository administrators about the new alert.

<a id="q3-15"></a>
## Q3.15 (ID 346656)

Which of the following workflow events would trigger a dependency review? (Each answer presents a complete solution. Choose two.)

⭕ **A.** commit
⭕ **B.** trigger
✅ **C.** workflow_dispatch
✅ **D.** pull_request

**Correct answer:** C, D
**Most voted:** CD

### Top explanations
- **0547a52** (1 upvotes [Most Recent, Selected Answer: CD]): D. pull_request
  Dependency review is primarily designed to run during pull requests to analyze dependency changes before merging. [docs.github.com]
  The dependency-review action is typically configured with on: [pull_request] and runs whenever a PR is opened, updated, or reopened.
  C. workflow_dispatch
  This is a manual trigger event in GitHub Actions, allowing you to run workflows (including dependency review) on demand.

<a id="q3-18"></a>
## Q3.18 (ID 346667)

How many alerts are created when two instances of the same secret value are in the same repository?

⭕ **A.** 4
⭕ **B.** 2
⭕ **C.** 3
✅ **D.** 1

**Correct answer:** D
**Most voted:** D

### Top explanations
- **0547a52** (3 upvotes [Most Recent, Selected Answer: D]): GitHub secret scanning de‑duplicates alerts for the same secret value. If the same secret appears multiple times, it does not create multiple alerts for each occurrence. Instead:
  A single alert is generated for that secret value.
  Even if it appears multiple times (e.g., repeated in files), it’s treated as one exposure to simplify triage.
  Supporting detail: GitHub documentation states that if the same secret appears multiple times (e.g., within a file), only one alert is created. [docs.github.com]
  So with two instances of the same secret value in the same repository → 1 alert
- **guhancse** (1 upvotes [Selected Answer: B]): It should be Option B. 2 alerts.

<a id="q3-24"></a>
## Q3.24 (ID 314130)

You are a maintainer of a repository and Dependabot notifies you of a vulnerability. Where could the vulnerability have been disclosed? (Each answer presents part of the solution. Choose two.)

⭕ **A.** in the National Vulnerability Database
⭕ **B.** in the dependency graph
✅ **C.** in security advisories reported on GitHub
⭕ **D.** in manifest and lock files

**Correct answer:** C
**Most voted:** C

### Top explanations
- **fe6c881** (1 upvotes [Most Recent, Selected Answer: C]): C.Dが正解。
  NVD などは GitHub Advisory Database の情報源として利用されますが、Dependabot が「どのリポジトリに影響するか」を判断する場ではない。
- **0a9a335** (1 upvotes [Selected Answer: A]): Dependabot alerts are generated based on vulnerability data from sources such as:
  The National Vulnerability Database (NVD), which is a public repository of security vulnerabilities.
  GitHub Security Advisories, which include both public and private advisories reported directly on GitHub.
  The dependency graph, manifest, and lock files are used to detect dependencies and their versions, but they are not where vulnerabilities are disclosed. They are used by Dependabot to check for known vulnerabilities.

<a id="q3-27"></a>
## Q3.27 (ID 316028)

What classification is used to categorize Dependabot alerts? Each correct answer presents part of the solution. (Choose three.)

✅ **A.** GitHub Security Advisory ID (GHSA)
⭕ **B.** Static Application Security Testing (SAST)
✅ **C.** Common Vulnerabilities and Exposures (CVE)
✅ **D.** Common Weakness Enumeration (CWE)
⭕ **E.** Exploit Prediction Scoring System (EPSS)

**Correct answer:** A, C, D
**Most voted:** ACD

### Top explanations
- **0a9a335** (3 upvotes [Most Recent, Selected Answer: ACD]): GitHub Security Advisory ID (GHSA): Unique identifiers for security advisories reported on GitHub.
  Common Vulnerabilities and Exposures (CVE): Standard identifiers for publicly known security vulnerabilities.
  Common Weakness Enumeration (CWE): A community-developed list of common software weakness types, often referenced in vulnerability descriptions.
  B. Static Application Security Testing (SAST) and E. Exploit Prediction Scoring System (EPSS) are not used to classify Dependabot alerts directly. SAST is a method for finding vulnerabilities, and EPSS is a scoring system for predicting exploit likelihood, but neither is a classification for Dependabot alerts.

<a id="q3-28"></a>
## Q3.28 (ID 315183)

Assuming that default security and analysis settings have not been changed at the repository, organization, or enterprise level, which scenario would generate a dependency graph for the repository?

✅ **A.** when a public repository has a new dependency added to its manifest file
⭕ **B.** when a private repository is forked to be used as a dependent
⭕ **C.** when a private repository has a new dependency added to its manifest file
⭕ **D.** when a public repository is forked to be used as a dependent

**Correct answer:** A
**Most voted:** A

### Top explanations
- **0a9a335** (3 upvotes [Most Recent, Selected Answer: A]): none of the scenarios would automatically generate a dependency graph for a private repository unless GHAS is enabled.
  However, public repositories do have the dependency graph enabled by default, so the correct answer under default settings (without GHAS) is A
- **ziggy1117** (2 upvotes [Selected Answer: A]): private repositories do not have it enabled by default.

<a id="q3-29"></a>
## Q3.29 (ID 315493)

What scenario demonstrates the use of Dependabot security updates?

⭕ **A.** An alert is created for a vulnerable dependency.
⭕ **B.** An alert is created for a secret that’s been exposed in the codebase.
✅ **C.** A pull request is opened that fixes a vulnerable dependency.
⭕ **D.** A pull request is opened that updates a dependency to the most recent version.

**Correct answer:** C
**Most voted:** C

### Top explanations
- **ziggy1117** (2 upvotes [Most Recent, Selected Answer: C]): https://learn.microsoft.com/en-us/training/modules/configure-dependabot-security-updates-on-github-repo/4-dependabot-security-updates
  Dependabot security updates are automated pull requests that help you update dependencies with known vulnerabilities.
  Dependabot version updates are automated pull requests that keep your dependencies updated, even when they don’t have any vulnerabilities.

<a id="q3-33"></a>
## Q3.33 (ID 315212)

What is the minimum role needed in order to view the secret scanning alerts list within the Security tab of a repository?

⭕ **A.** Read
⭕ **B.** Write
⭕ **C.** repository owner
✅ **D.** Admin

**Correct answer:** D
**Most voted:** D

### Top explanations
- **ivantsanev** (3 upvotes [Selected Answer: D]): The minimum role needed to view the secret scanning alerts list within the Security tab of a repository is the Admin role. While a repository owner inherently has this access, "Admin" is the specific role permission level required.
- **0547a52** (2 upvotes [Most Recent, Selected Answer: D]): D. Admin
  For GitHub Secret Scanning Alerts (especially in private/internal repositories), visibility is restricted to:
  Repository Admins
  Organization owners
  Security managers
  Repository owners (personal repos)
- **ziggy1117** (2 upvotes [Selected Answer: B]): Write:
  https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization#access-requirements-for-security-features
  View and dismiss secret scanning alerts in a repository - Write is needed a minimum

<a id="q4-6"></a>
## Q4.6 (ID 346629)

How would you build your code within the CodeQL analysis workflow? Each answer presents a complete solution. (Choose two.)

⭕ **A.** Upload compiled binaries.
✅ **B.** Use CodeQL’s autobuild action.
⭕ **C.** Use jobs.analyze.runs-on.
⭕ **D.** Use CodeQL’s init action.
⭕ **E.** Ignore paths.
✅ **F.** Implement custom build steps.

**Correct answer:** B, F
**Most voted:** BF

### Top explanations
- **0547a52** (1 upvotes [Most Recent, Selected Answer: BF]): In a CodeQL analysis workflow, there are two supported ways to build your code:
  B. Use CodeQL’s autobuild action ✅
  CodeQL provides an autobuild step that automatically detects and builds your project.
  This is the simplest and recommended option when your project uses a common build system.
  F. Implement custom build steps ✅
  If autobuild doesn’t work (e.g., complex or custom build process),
  You can define your own manual build steps in the workflow.

<a id="q4-10"></a>
## Q4.10 (ID 315494)

When secret scanning detects a set of credentials on a public repository, what does GitHub do?

⭕ **A.** It sends a notification to repository members.
⭕ **B.** It displays a public alert in the Security tab of the repository.
✅ **C.** It notifies the service provider who issued the secret.
⭕ **D.** It scans the contents of the commits for additional secrets.

**Correct answer:** C
**Most voted:** C

### Top explanations
- **0547a52** (2 upvotes [Most Recent, Selected Answer: C]): Copilot said: Correct answer: C. It notifies the service provider who issued the secret.
  ✅ Explanation
  When secret scanning detects credentials in a public repository, GitHub performs a partner alert action:
  GitHub notifies the service provider (issuer of the secret) so they can take immediate action (e.g., revoke the credential). [docs.github.com]
  These are called partner alerts, and they are sent directly to the provider, not shown publicly in the repo. [docs.github.com]

<a id="q4-11"></a>
## Q4.11 (ID 315213)

As a developer with write access, you navigate to a code scanning alert in your repository. When will GitHub close this alert?

⭕ **A.** after you triage the pull request containing the alert
✅ **B.** after you fix the code by committing within the pull request
⭕ **C.** when you use data-flow analysis to find potential security issues in code
⭕ **D.** after you find the code and click the alert within the pull request

**Correct answer:** B
**Most voted:** B

### Top explanations
- **0547a52** (2 upvotes [Most Recent, Selected Answer: B]): Correct answer: B. after you fix the code by committing within the pull request
  ✅ Explanation
  GitHub closes a code scanning (CodeQL) alert when the underlying issue is actually fixed in the codebase:
  When you fix the vulnerable code and commit the change (usually via a pull request),
  A new code scan runs, and
  If the issue is no longer detected, the alert is automatically resolved (closed).
  This aligns with how GitHub handles alerts: they remain open until the vulnerability or issue is removed from the code during analysis. [docs.github.com]
- **0a9a335** (2 upvotes [Selected Answer: B]): The vulnerable code is fixed (e.g., the security issue is resolved) and the fix is committed to the repository.
  The fix is merged into the default branch (or the branch where the alert was originally detected).

<a id="q4-32"></a>
## Q4.32 (ID 315496)

What is a benefit of using a custom CodeQL configuration file?

⭕ **A.** It allows you to schedule the scan.
⭕ **B.** It allows configuration options for multiple repositories in a single place.
✅ **C.** It disables packs from running the default query suite.
⭕ **D.** It specifies a token that has access to the private repository.

**Correct answer:** C
**Most voted:** C

### Top explanations
- **ziggy1117** (3 upvotes [Most Recent, Selected Answer: C]): A custom configuration file is an alternative way to specify additional packs and queries to run. You can also use the file to disable the default queries and to specify which directories to scan during analysis.
  https://learn.microsoft.com/en-us/training/modules/code-scanning-with-github-codeql/8-customize-your-scanning-workflow-with-codeql-2

<a id="q5-1"></a>
## Q5.1 (ID 314580)

Which of the following tasks can be performed by a security team as a proactive measure to help address secret scanning alerts? Each answer presents a complete solution. (Choose two.)

⭕ **A.** Enable system for cross-domain identity management (SCIM) provisioning for the enterprise.
✅ **B.** Document alternatives to storing secrets in the source code.
⭕ **C.** Dismiss alerts that are older than 90 days.
⭕ **D.** Configure a webhook to monitor for secret scanning alert events.

**Correct answer:** B
**Most voted:** B

### Top explanations
- **tdkc** (3 upvotes [Most Recent, Selected Answer: B]): Choose 2 = B & D
  B. Document alternatives to storing secrets in the source code.
  D. Configure a webhook to monitor for secret scanning alert events.

<a id="q5-3"></a>
## Q5.3 (ID 315214)

Which of the following formats are used to describe a Dependabot alert? Each answer presents a complete solution. (Choose two.)

⭕ **A.** Vulnerability Exploitability eXchange (VEX)
✅ **B.** Common Vulnerabilities and Exposures (CVE)
✅ **C.** Common Weakness Enumeration (CWE)
⭕ **D.** Exploit Prediction Scoring System (EPSS)

**Correct answer:** B, C
**Most voted:** BC

### Top explanations
- **ivantsanev** (3 upvotes [Most Recent, Selected Answer: BC]): ependabot alerts are generated based on entries in the GitHub Advisory Database, and these entries use established security classifications to describe the vulnerability.
  B. Common Vulnerabilities and Exposures (CVE): Each Dependabot alert is linked to a security advisory that typically has a CVE ID. CVE is a public list of all known cybersecurity vulnerabilities, providing a standardized identifier for the issue.
  C. Common Weakness Enumeration (CWE): The advisory details for a Dependabot alert often map the vulnerability to a specific type of software flaw or weakness, which is identified by a CWE ID.
