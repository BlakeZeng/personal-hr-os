# Personal HR OS · Employee Lifecycle Preview

Build your own AI workspace for HR, starting with employee onboarding. In this preview, use Codex to prepare an onboarding handover. The example begins with a new joiner and includes movements and exits so you can see how the same workflow handles different events. You get a private workspace with two project skills, a fictional roster and event list, and editable case and handover templates.

## Install for Codex

Use a Mac or Linux computer with Python 3.9 or later, Git, and a signed-in Codex app or CLI. Open a terminal and run:

```sh
git clone https://github.com/BlakeZeng/personal-hr-os.git
cd personal-hr-os
python3 install.py "$HOME/My Personal HR OS"
```

Choose a different new private folder if you prefer. Its parent must already exist. Setup creates the workspace outside the downloaded source, verifies its files and links both skills inside that workspace. If the destination already exists, setup stops so you can keep its records. If you downloaded the repository with **Code → Download ZIP**, extract it, open a terminal in the extracted folder and run the Python command above.

## Run your first onboarding case

Open **My Personal HR OS** as a project in Codex and start a fresh chat. Paste this request:

> Use the project’s $skillos-blake1 and $employee-lifecycle-record-preparation to run the fictional onboarding case. Follow Context/Guides/Lifecycle Pilot.md and the BASE request for all event rows. I authorise saving the case record, one Case Index entry and the draft handover in this private workspace. Reopen the saved handover, tell me which events are ready for HR review and which need correction, and link me to the file.

If prompted to trust the project, review the folder you chose. If you already have a skill named Blake1, confirm Codex selects the copy inside this project. Both discovery links live in `.agents/skills/` and resolve to the local `Skills/_Drafts/` folder.

## Find the handover

Open `Work/Outputs/SSC-T-20261117-001-lifecycle-handover.md` **in My Personal HR OS**. Codex creates it when the case runs. It should account for all seven events, show the proposed fields, explain each hold, and name the source owner and receiving HR reviewer. The companion record is `Work/Records/SSC-T-20261117-001.md`. An unchanged repeat reuses the same case and index entry.

[Blank handover template](Work/Templates/Lifecycle%20Record%20Handover.md) · [Fictional input and case instructions](Context/Guides/Lifecycle%20Pilot.md) · [Included skills](Skill%20Index.md)

## Scope and licence

This source-available preview supports local file practice on fictional data. Its two Draft skills prepare evidence for HR review. Human owners retain employment decisions, source corrections and receiving acceptance. Both a real employee-system update and the use of real people’s data require separate local authority.

Copyright © 2026 Blake. Personal and internal HR use are free, including at a for-profit employer. Selling the OS or an adaptation containing its materials requires Blake’s prior written permission. See the [licence](LICENSE) and [adaptation notice](NOTICE.md).
