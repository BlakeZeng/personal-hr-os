# Personal HR OS · Employee Lifecycle Preview

Build your own AI workspace for HR, starting with employee onboarding. In this preview, use Codex to prepare an onboarding handover. The example begins with a new joiner and includes movements and exits so you can see how the same workflow handles different events. You get a private workspace with two project skills, a fictional roster and event list, and editable case and handover templates.

## Install for Codex

On a Mac or Linux computer with Git, Python 3.9 or later, and a signed-in Codex app or CLI, paste this into Codex:

> Install Personal HR OS from https://github.com/BlakeZeng/personal-hr-os. Ask me where to put my private workspace.

Reply with the path for a new folder. For example, if your Documents folder exists, you could choose `~/Documents/My HR Workspace`. Codex will give you the folder to open as a project. It contains both skills, the fictional inputs, and a place for your case records.

**For Codex handling setup:** Ask for the destination before creating the workspace. If someone shares only the link, first ask whether they want to install it. After they choose a new folder in an existing parent, fetch this public repository into a separate temporary checkout. Inspect and run its `install.py` with their choice as the single workspace argument. Use the project installer so both skills and their templates stay together. Report the verified install location, give the user a clickable local link to its README, and invite them to open that folder in Codex for the first case. If the destination exists, leave it in place and ask for a new folder name.

### Manual installation

If you prefer the terminal, run:

```sh
git clone https://github.com/BlakeZeng/personal-hr-os.git
cd personal-hr-os
python3 install.py "$HOME/My Personal HR OS"
```

Choose a different new private folder if you prefer. Its parent must already exist. Setup creates the workspace outside the downloaded source, verifies its files and links both skills inside that workspace. If the destination already exists, setup stops so you can keep its records. If you downloaded the repository with **Code → Download ZIP**, extract it, open a terminal in the extracted folder and run the Python command above.

## Run your first onboarding case

Open the **private folder you chose** as a project in Codex. Start a fresh chat and say:

> Blake1, run the sample onboarding case.

Asking Blake1 to run the sample tells it to save the fictional case record, its index entry, and a draft handover in this workspace. Blake1 chooses the employee lifecycle skill, checks the saved handover, and returns a link you can open.

## Find the handover

Open the handover link in Blake1’s reply. You can also open `Work/Outputs/SSC-T-20261117-001-lifecycle-handover.md` in your private folder. Codex creates it when the case runs. It should account for all seven events, show the proposed fields, explain each hold, and name the source owner and receiving HR reviewer. The companion record is `Work/Records/SSC-T-20261117-001.md`. An unchanged repeat reuses the same case and index entry.

[Blank handover template](Work/Templates/Lifecycle%20Record%20Handover.md) · [Fictional input and case instructions](Context/Guides/Lifecycle%20Pilot.md) · [Included skills](Skill%20Index.md)

## Update an existing workspace

Open the existing private folder as a project in Codex and paste this request:

> Update this Personal HR OS workspace in place from https://github.com/BlakeZeng/personal-hr-os. Keep my organisation profile, case index and saved handovers.

Codex downloads the current release separately and runs its updater against the folder you already use. Your organisation profile, case index, case records and saved handovers stay in place. If you edited a file supplied with the OS, the updater keeps your edit. If the new release also changes that file, or needs a new file path that already contains different local content, the updater stops before applying changes and lists the affected paths. Keep a copy of your work while resolving the conflict before trying again. After a successful update, start a fresh chat in the same project.

**For Codex handling an update:** Use the current project if it is the user's private Personal HR OS workspace. Otherwise ask for the existing workspace path. Fetch a fresh copy of this repository outside that workspace, inspect its installer and run `python3 install.py --update` with the existing workspace path as its argument. Report the folder you updated, the updater's result and any paths it kept for review. If the updater stops, report its reason and preserve the existing folder.

### Manual update

On Mac or Linux with Git and Python 3.9 or later, replace the example workspace path below with the path you originally chose.

```sh
release_dir=$(mktemp -d)
git clone --depth 1 https://github.com/BlakeZeng/personal-hr-os.git "$release_dir/personal-hr-os"
python3 "$release_dir/personal-hr-os/install.py" --update "$HOME/Documents/My HR Workspace"
```

## Scope and licence

This source-available preview supports local file practice on fictional data. Its two Draft skills prepare evidence for HR review. Human owners retain employment decisions, source corrections and receiving acceptance. Both a real employee-system update and the use of real people’s data require separate local authority.

Copyright © 2026 Blake. Personal and internal HR use are free, including at a for-profit employer. Selling the OS or an adaptation containing its materials requires Blake’s prior written permission. See the [licence](LICENSE) and [adaptation notice](NOTICE.md).
