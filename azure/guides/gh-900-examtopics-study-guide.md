# GH-900 GitHub Foundations Study Guide

_19 questions generated from ExamTopics discussions._

## Table of contents

- [Q1.1](#q1-1)
- [Q1.2](#q1-2)
- [Q1.3](#q1-3)
- [Q1.4](#q1-4)
- [Q1.11](#q1-11)
- [Q1.15](#q1-15)
- [Q1.20](#q1-20)
- [Q1.22](#q1-22)
- [Q1.34](#q1-34)
- [Q2.22](#q2-22)
- [Q3.11](#q3-11)
- [Q3.17](#q3-17)
- [Q4.4](#q4-4)
- [Q4.16](#q4-16)
- [Q5.2](#q5-2)
- [Q5.4](#q5-4)
- [Q5.10](#q5-10)
- [Q6.11](#q6-11)
- [Q6.16](#q6-16)

<a id="q1-1"></a>
## Q1.1 (ID 313403)

Which of the following keywords are used to link a pull request to an issue? (Choose three.)

✅ **A.** fix
✅ **B.** resolves
⭕ **C.** merge
⭕ **D.** join
✅ **E.** closed
⭕ **F.** connects

**Correct answer:** A, B, E
**Most voted:** ABE

### Top explanations
- **CamTien** (2 upvotes [Selected Answer: ABE]): fix
  resolves
  closed
- **ysuzukix** (1 upvotes [Most Recent, Selected Answer: ABE]): On GitHub, you can link a pull request to an issue to automatically close the issue when the pull request is merged. This is done by using specific keywords followed by the issue number (e.g., #42) in the PR description or commit messages.
- **Cooljoy7777** (1 upvotes [Selected Answer: ABE]): closes
  fixes
  resolves
  Other variations like "closed", "fixed", "resolved", "close", "fix", and "resolve"

<a id="q1-2"></a>
## Q1.2 (ID 313390)

Which syntax is used for authoring saved replies?

⭕ **A.** HTML
⭕ **B.** YAML
⭕ **C.** Markup
✅ **D.** Markdown

**Correct answer:** D
**Most voted:** D

### Top explanations
- **Cooljoy7777** (2 upvotes [Selected Answer: D]): The correct syntax for authoring saved replies is Markdown. This simple markup language allows for easy formatting of text and can be converted to HTML. It is widely used due to its user-friendly nature and versatility
- **ysuzukix** (1 upvotes [Most Recent, Selected Answer: D]): GitHub's "Saved replies" feature allows you to store commonly used text for issue or pull request comments so you can efficiently reuse them.
  Just like most text fields and comment boxes on GitHub, saved replies fully support Markdown syntax. By using Markdown, you can easily include formatting such as bold text (), bullet points (-), hyperlinks, and code blocks (```) in your templates.

<a id="q1-3"></a>
## Q1.3 (ID 313372)

As a user, what feature can you use to merge proposed changes in a repository on GitHub?

⭕ **A.** discussions
⭕ **B.** projects
✅ **C.** pull requests
⭕ **D.** issues

**Correct answer:** C
**Most voted:** C

### Top explanations
- **ysuzukix** (1 upvotes [Most Recent, Selected Answer: C]): In GitHub, the core feature used to propose, review, and merge code changes into a repository's branch is the Pull Request.
  It allows developers to visually check the differences in code, discuss the changes, and safely merge them once they are approved.
- **abdx** (1 upvotes [Selected Answer: C]): pull requests obviously

<a id="q1-4"></a>
## Q1.4 (ID 312523)

If there are multiple README files, which of the following locations will be displayed first?

⭕ **A.** docs
⭕ **B.** root
⭕ **C.** src
✅ **D.** .gitHub

**Correct answer:** D
**Most voted:** D

### Top explanations
- **Deequation** (3 upvotes [Selected Answer: D]): While the answer 'root' makes sense from the old days. Now days, the .github folder is used to store a lot of the markdown files, that makes up a repository, and these actually take priority, over files located in the root. I had to try this out myself - and it absolutely does use the file in .github. The documentation, which you can easily find, says the following:
  "If a repository contains more than one README file, then the file shown is chosen from locations in the following order: the .github directory, then the repository's root directory, and finally the docs directory."
  Let this be a good reminder, to structure your repositories better, and get rid of all the markdown files from the root.
- **ETU69** (1 upvotes [Most Recent]): Yes. Correct. Did the test myself as well.
- **santa3456** (1 upvotes [Selected Answer: D]): When a repository contains multiple README files in different locations, the file displayed first is chosen based on a specific order of precedence.
  This order is as follows:
  .github directory: A README file located within the .github directory takes the highest precedence.
  Repository's root directory: If no README is found in .github, the system will then look for a README in the main root directory of the repository.
  docs directory: If no README is found in either of the above locations, the system will finally check the docs directory for a README file.
- **PawanDev** (1 upvotes [Selected Answer: B]): In GitHub, when a repository is displayed, the README file shown on the main page is the one located in the root of the repository.
  README files in subfolders like docs, src, or .github are not displayed by default on the main repository page; they are only shown when navigating to that folder.
- **Vikram1710** (1 upvotes [Selected Answer: B]): It should be Root

<a id="q1-11"></a>
## Q1.11 (ID 313422)

How can a user resume an existing Codespace that is bound to a repository? (Choose two.)

⭕ **A.** Browse to the repository in GitHub.com and press the period “.” key.
⭕ **B.** Use the git CLI with the codespace parameter (e.g., "git codespace code -web").
✅ **C.** Open https://github.com/codespaces in the browser, select the repository, and then select the existing Codespace.
✅ **D.** Browse to the repository in GitHub.com, press the comma “,” key and select Resume this codespace.

**Correct answer:** C, D
**Most voted:** CD

### Top explanations
- **J** (1 upvotes [Most Recent, Selected Answer: CD]): https://docs.github.com/en/codespaces/developing-in-a-codespace/opening-an-existing-codespace

<a id="q1-15"></a>
## Q1.15 (ID 313376)

Which GitHub tools or features is best to quickly modify a batch of files in a repository?

✅ **A.** Use github.dev from a web browser.
⭕ **B.** Install and use the git CLI.
⭕ **C.** Create and use a new GitHub Codespace.
⭕ **D.** Install and use GitHub Desktop.
⭕ **E.** Install and use GitHub Mobile.

**Correct answer:** A
**Most voted:** A

### Top explanations
- **tfaw** (2 upvotes [Most Recent, Selected Answer: A]): A is probably the quickest as it requires no installation.
- **vitobeg** (1 upvotes [Selected Answer: A]): no install, quick way
- **b0b2c3c** (1 upvotes [Selected Answer: D]): I think multiple answers are possible and it should be A-B-D

<a id="q1-20"></a>
## Q1.20 (ID 313429)

What qualifier finds issues that mention a certain user?

⭕ **A.** threads:
⭕ **B.** mentions:
✅ **C.** mentioned:
⭕ **D.** @mentioned:

**Correct answer:** C
**Most voted:** C

### Top explanations
- **GodArrived** (1 upvotes [Most Recent, Selected Answer: C]): • How it works: The mentioned:USERNAME qualifier filters search results to show issues or pull requests that explicitly include a specific user's GitHub username in the description or comments.
  • Why the others are incorrect:
  • mentions: is not a valid search qualifier.
  • threads: does not exist for filtering user mentions.
  • @mentioned: is incorrect because the @ symbol is used to tag users in comments, but the search syntax itself does not include the @ symbol before the qualifier name.

<a id="q1-22"></a>
## Q1.22 (ID 313368)

What is the primary goal of GitHub in terms of integrating tools and providing an ecosystem?

✅ **A.** to bring developers’ preferred tools together in one place
⭕ **B.** to offer a diverse range of tools for specific development needs
⭕ **C.** to develop proprietary tools and provide opinionated integration options
⭕ **D.** to create a unified, standardized ecosystem for all developers

**Correct answer:** A
**Most voted:** A

### Top explanations
- **GodArrived** (1 upvotes [Most Recent, Selected Answer: A]): Correct answer: A. to bring developers’ preferred tools together in one place.
  GitHub’s primary goal is to integrate developers’ preferred tools into one platform, enabling seamless collaboration and a flexible development workflow without forcing everyone to use the same tools.

<a id="q1-34"></a>
## Q1.34 (ID 426671)

What information can you find in the “Checks” tab of a pull request?

✅ **A.** The pull request description and timeline of events
✅ **B.** A summary of all changes made to the repository
✅ **C.** Comments left by reviewers on specific lines of code.
✅ **D.** A list of all commits included in the pull request

**Correct answer:** A, B, C, D
**Most voted:** ABCD

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: ABCD]): None of the answers is correct, double checked.
  None of the listed options correctly describes the Checks tab.
  GitHub’s official documentation says the Checks tab shows automated tests, builds, and other validations, including whether checks passed or failed, plus detailed output such as logs, annotations, and test results. GitHub Docs
  For comparison:
  - A. ❌ Pull request description and timeline → Conversation tab
  - B. ❌ Summary of all repository changes → not what Checks shows
  - C. ❌ Reviewer comments on specific lines → mainly Files changed / review comments
  - D. ❌ List of commits → Commits tab
  So this question appears to be missing the correct answer option.
  The correct concept would be something like:
  “The results of automated tests, builds, and other status checks.”

<a id="q2-22"></a>
## Q2.22 (ID 402581)

The difference between GitHub Desktop and github.com is that Desktop:

⭕ **A.** enables integration with office suite applications.
⭕ **B.** is only available on Windows operating systems.
✅ **C.** offers a graphical user interface.
⭕ **D.** is a self-hosted version of GitHub.
⭕ **E.** is a standalone software application.

**Correct answer:** C
**Most voted:** C

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: C]): GitHub Desktop is an installed standalone desktop application. GitHub.com is the web-based GitHub service; both provide graphical interfaces, so that alone is not the distinguishing characteristic.

<a id="q3-11"></a>
## Q3.11 (ID 402583)

How can a user choose to receive ongoing updates about a specific activity on GitHub.com?

⭕ **A.** by subscribing to notifications for all activity in a repository
⭕ **B.** by upgrading from a free to a paid account
⭕ **C.** by automatically watching all repositories you have push access to
✅ **D.** by customizing the types of notifications you will receive in the future

**Correct answer:** D
**Most voted:** D

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: D]): D. by customizing the types of notifications you will receive in the future ✅
  On GitHub.com, users can choose how they want to receive ongoing updates by configuring their notification settings and selecting the kinds of activity they want to be notified about
  .
  - A. ❌ Watching an entire repository is one option, but the question asks more generally how to choose ongoing updates about specific activity.
  - B. ❌ Paid plans are not required for notification controls.
  - C. ❌ GitHub does not automatically watch every repository you can push to.
  - D. ✅ Correct

<a id="q3-17"></a>
## Q3.17 (ID 402589)

What are some scenarios that can automatically subscribe you to conversations on GitHub? (Choose three.)

⭕ **A.** being added as a repo admin
⭕ **B.** pushing a commit to the default branch
✅ **C.** opening a pull request or issue
✅ **D.** being assigned to an issue or pull request
✅ **E.** commenting on a thread

**Correct answer:** C, D, E
**Most voted:** CDE

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: CDE]): The correct answers are C, D, and E. ✅
  GitHub’s official documentation says you are automatically subscribed to a conversation when you:
  - C. open a pull request or issue ✅
  - D. are assigned to an issue or pull request ✅
  - E. comment on a thread ✅ GitHub Docs
  Why the others are wrong:
  - A. being added as a repo admin ❌ — that does not by itself subscribe you to every conversation.
  - B. pushing a commit to the default branch ❌ — pushing a commit does not automatically subscribe you to issue/PR conversations in general.
  GitHub also lists other automatic-subscription cases, such as being @mentioned, manually subscribing, or changing the state of a thread.

<a id="q4-4"></a>
## Q4.4 (ID 313427)

Copilot for Individuals offers which of the following features that are not offered by Copilot for Business? (Choose two.)

✅ **A.** VPN proxy support via self-signed certificates
⭕ **B.** organization-wide policy management
⭕ **C.** telemetry
⭕ **D.** blocks suggestions matching public code
⭕ **E.** offers multi-line function suggestions
✅ **F.** support for personal GitHub accounts

**Correct answer:** A, F
**Most voted:** AF

### Top explanations
- **tfaw** (2 upvotes [Selected Answer: AF]): I agree with AF
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: CF]): So for this older exam question, I would now rank the likely intended answers as:
  - C. telemetry ✅
  - F. support for personal GitHub accounts ✅
  And I would remove D. Today, blocking suggestions that match public code is configurable for both personal and organization-managed Copilot plans, so it is not a clean Individuals-only feature.
- **b0b2c3c** (1 upvotes [Selected Answer: AF]): public code matching is available in Business. I think it is self signed ceritifactes and personal account.

<a id="q4-16"></a>
## Q4.16 (ID 402598)

Which of the following items can you customize for an individual Codespace? (Choose three.)

⭕ **A.** operating system
⭕ **B.** branch protections
✅ **C.** name
✅ **D.** default editor
✅ **E.** shell

**Correct answer:** C, D, E
**Most voted:** CDE

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: CDE]): The correct answers are C, D, and E. ✅
  GitHub’s official Codespaces documentation confirms that you can customize:
  - C. name ✅ — you can rename an individual codespace. GitHub Docs
  - D. default editor ✅ — you can choose whether Codespaces opens in VS Code web, VS Code desktop, or JupyterLab. GitHub Docs
  - E. shell ✅ — you can change the shell used in a codespace. GitHub Docs
  Why not the others:
  - A. operating system ❌ — Codespaces uses a Linux-based environment; you can change the container image/configuration, but you do not choose Windows or macOS as the codespace OS in the normal sense.
  - B. branch protections ❌ — branch protection is a repository setting, not a per-codespace customization.

<a id="q5-2"></a>
## Q5.2 (ID 313408)

Which of the following default workflows are available as part of GitHub projects? (Choose three.)

✅ **A.** “Auto-archive items”
⭕ **B.** “Label added to issue”
✅ **C.** “Item closed”
✅ **D.** “Pull request merged”
⭕ **E.** “Pull request opened”

**Correct answer:** A, C, D
**Most voted:** ACD

### Top explanations
- **b0b2c3c** (3 upvotes [Selected Answer: ACD]): This seems incorrect. After creating a project you get these workflows:
  - Auto-add sub-issues to project
  - Auto-close issue
  - Item added to project
  -Item closed
  - Pull request linked to issue
  - Pull request merged
  - Auto-add to project
  -Auto-archive items
  - Code changes requested
  - Code review approved
  - Item reopened
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: ACD]): The correct answers are A, C, and D. ✅
  GitHub Projects includes built-in/default workflows such as:
  - A. “Auto-archive items” ✅ — automatically archives project items that match configured criteria. GitHub Docs
  - C. “Item closed” ✅ — when an issue or pull request in the project is closed, its status can automatically be set to Done. GitHub Docs
  - D. “Pull request merged” ✅ — when a pull request is merged, its project status can automatically be set to Done. GitHub Docs
  Why not the others:
  - B. “Label added to issue” ❌ — not one of the standard built-in Project workflows.
  - E. “Pull request opened” ❌ — this is not one of the default built-in workflows listed by GitHub Projects.

<a id="q5-4"></a>
## Q5.4 (ID 313406)

What are advantages of GitHub Projects over GitHub Projects Classic? (Choose two.)

⭕ **A.** GitHub Projects can be connected to third-party tools.
✅ **B.** GitHub Projects has Insights.
✅ **C.** GitHub Projects has multiple layout views.
⭕ **D.** GitHub Projects are Copilot enabled.

**Correct answer:** B, C
**Most voted:** BC

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: BC]): The correct answers are B and C. ✅
  GitHub’s current Projects experience adds capabilities that Projects (Classic) did not have in the same way:
  - B. GitHub Projects has Insights ✅ — Projects supports configurable charts and Insights based on project data. GitHub Docs
  - C. GitHub Projects has multiple layout views ✅ — you can view the same project as a table, board, or roadmap, and create multiple customized views with filtering, sorting, and grouping. GitHub Docs
  Why not the others:
  - A. ❌ Third-party integrations are not the key differentiating advantage being tested here.
  - D. ❌ “Copilot enabled” is not a defining GitHub Projects vs Projects Classic distinction.
  One useful current note: Projects (Classic) has been deprecated and was removed in 2025, so this question reflects an older comparison that is still common in exam banks.
- **b0b2c3c** (1 upvotes [Selected Answer: BC]): They both seem to have Copilot enabled. Should be BC.

<a id="q5-10"></a>
## Q5.10 (ID 402603)

What layouts are available for GitHub Projects? (Choose three.)

✅ **A.** Table
✅ **B.** Roadmap
⭕ **C.** Backlog
✅ **D.** Board
⭕ **E.** Kanban

**Correct answer:** A, B, D
**Most voted:** ABD

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: ABD]): The correct answers are A, B, and D. ✅
  GitHub Projects supports three main layout types:
  - A. Table ✅ — spreadsheet-like view of project items and fields
  - B. Roadmap ✅ — timeline-based planning view
  - D. Board ✅ — column-based workflow view
  Why the others are wrong:
  - C. Backlog ❌ — backlog can be represented within a project, but it is not one of the named layout types.
  - E. Kanban ❌ — the Board layout is the Kanban-style view; “Kanban” itself is not the layout name.

<a id="q6-11"></a>
## Q6.11 (ID 402608)

When using Organizations, GitHub Teams is better than GitHub Free because it offers:

⭕ **A.** advanced tools and insights in private repositories.
✅ **B.** increased GitHub Actions minutes and additional GitHub Packages storage.
⭕ **C.** authentication with SAML single sign-on and increased GitHub Actions minutes.
⭕ **D.** expanded storage and priority support.

**Correct answer:** B
**Most voted:** B

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: B]): B. increased GitHub Actions minutes and additional GitHub Packages storage ✅
  According to GitHub’s current official plan documentation, GitHub Team includes more usage than GitHub Free for organizations:
  - GitHub Actions: 3,000 minutes/month vs. 2,000
  - GitHub Packages storage: 2 GB vs. 500 MB GitHub Docs
  Why not the others:
  - A. ❌ Advanced tools and insights in private repositories are associated with paid plans, but this wording is more characteristic of GitHub Pro for personal accounts; the clearest Team-vs-Free organization distinction in these options is the increased Actions minutes and Packages storage. GitHub Docs
  - C. ❌ SAML SSO is an Enterprise feature, not GitHub Team. github.com
  - D. ❌ Priority support is also an Enterprise-level benefit, not standard GitHub Team.

<a id="q6-16"></a>
## Q6.16 (ID 426674)

Which three of the following types of secrets can GitHub Push Protection detect? Each answer presents a complete solution.
NOTE: Each correct selection is worth one point.

⭕ **A.** Hardcoded email addresses
⭕ **B.** Code formatting issue
⭕ **C.** Database connection strings
✅ **D.** SSH private keys
✅ **E.** OAuth tokens
✅ **F.** API Keys

**Correct answer:** D, E, F
**Most voted:** DEF

### Top explanations
- **Kiwi28** (1 upvotes [Most Recent, Selected Answer: DEF]): The correct answers are D, E, and F. ✅
  GitHub Push Protection is designed to detect and block supported secrets before they are pushed. GitHub’s official secret-scanning documentation lists private keys and many provider-specific tokens/keys as supported secret types. GitHub Docs
  - A. Hardcoded email addresses ❌ — not treated as secrets.
  - B. Code formatting issue ❌ — unrelated to secret scanning.
  - C. Database connection strings ❌ — GitHub secret scanning can detect some connection strings, but generic connection-string patterns are not generally covered by default push protection in the way this exam question is targeting. GitHub Docs
  - D. SSH private keys ✅
  - E. OAuth tokens ✅
  - F. API Keys ✅
