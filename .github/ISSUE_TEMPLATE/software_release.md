---
name: remarx release checklist
about: Checklist for releasing new versions of remarx
title: remarx release checklist
labels: ''
assignees: ''

---

## release prep

- [ ] Pull updated copies of the develop and main branches
- [ ] Use git flow to create a new release branch with the appropriate version (e.g., `git flow release start 0.5`)

### prep release candidate for acceptance testing

- [ ] Update the version number in `src/remarx/__init__.py` to the appropriate release candidate number (e.g., `0.5rc1`)
- [ ] Create a draft PR (since it should not be merged)
- [ ] Review the changelog to make sure that all features, changes, bugfixes, etc included in the release are documented. You may want to review the git revision history to be sure you've captured everything.
- [ ] Review the README to make sure that its contents are up to date
- [ ] Check python requirements for any internal dependencies that should be released (or at least pinned to a specific git commit)
- [ ] Confirm that all checks for the draft PR pass (e.g., unit tests, code coverage checks)
- [ ] Build documentation on the release branch and run the server to review and make sure it is up to date.
- [ ] Make sure code documentation covers all the files in the code.

### BEFORE acceptance testing

- [ ] Review issues included in the release to make sure they have testing instructions before marking them as ready for acceptance testing.
- [ ] Give project team members instructions about how to install the release candidate version.

### IF acceptance testing fails

*These steps are only needed if acceptance testing fails and you need to update and retest the release candidate.*

- [ ] Increment the version number to the next release candidate (e.g., `0.5rc1` → `0.5rc2`)
- [ ] Address the changes raised in acceptance testing and repeat the previous section.

### WHEN acceptance testing passes

- [ ] Set the final release version number (e.g., `0.5rc1` → `0.5`)
- [ ] Use git flow to finish the release (merge release branch into both main and develop, create a tag, remove the release branch, etc.). (`git flow release finish 0.5`)

## after release

- [ ] Increase the develop branch version so it is set to the next expected release (i.e., if you just released `0.5` then develop will probably be `0.6.dev0` unless you are working on a major update, in which case it will be `1.0.dev0`)
- [ ] Push all updates to GitHub (main branch, develop branch, tags)
- [ ] Create a GitHub release for the new tag, to trigger package publication on PyPI (and eventually Zenodo DOI)
