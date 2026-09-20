# Project collaboration

- Work on one small, understandable milestone at a time. Explain changes and validation, then let the user test phone-dependent behavior before proceeding to the next milestone.
- The user has authorized committing and pushing completed milestones to `https://github.com/flowbaka/pothole_detection_website.git`. Use the configured `origin`; do not request the same authorization again for ordinary milestone pushes.
- Review the diff and staged file list before committing. Keep the virtual environment, certificates/private keys, secrets, private video/location data and large model weights out of Git. Preserve unrelated user changes.
- Use meaningful commit messages. Check remote history before pushing, preserve existing commits, and never force-push without specific authorization. Report the resulting commit and whether the push succeeded.
- Distinguish automated checks with simulated devices from results confirmed on actual phones. Never claim a device test passed without evidence.
- GitHub source pushes do not authorize deploying or hosting the website publicly.
