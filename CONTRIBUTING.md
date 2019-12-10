# Contributing
Thanks for taking the time to contribute!

This document discusses guidelines for contributing to NeuRec, please read them and use your best judgement when providing changes. Feel free to propose changes with a pull request.

This repository uses [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) for submitting changes.

## Table of Contents
* [Important Resources](#Important-Resources)
* [Suggest Enhancements](#Suggest-Enhancements)
* [Pull Requests](#Pull-Requests)
* [Style Guides](#Style-Guides)
  * [Git commit messages](#Git-commit-messages)
  * [Documentation](#Documentation)

## Important Resources
Here is a list of links to important resources for the project:
* documentation - found in the [docs folder](/docs)
* bugs - please use the [Issues tab](https://github.com/NExTplusplus/NeuRec/issues)
* license - [LICENSE file](/LICENSE)
* change log - [CHANGELOG file](/CHANGELOG.md)

## Suggest Enhancements
Before submitting a suggestion for enhancement, please check the CHANGELOG file to see whether the enhancement has already been implemented or is scheduled for a future release. Additionally, please search through the Issues tab to see if the enhancement has already been suggested.

To submit enhancement suggestion, please use the Issues tab and include as much detail as possible.

## Pull Requests
Please follow these steps to have your contribution considered by the maintainers:
* Follow the Style Guides
* Update project documentation files, such as README.md and CHANGELOG.md
* Clean the commit history, e.g. squash smaller commits into larger commits
* Provide as much detail as possible about the proposed changes
* Propose changes early by creating a pull request, labelled with **WIP:** at the beginning of the title.
* Before merging a release branch, update the CHANGELOG.md file with a new version number. After merging, add a new tag on master with the same version number.

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Style Guides
This section discusses styling guides for the different aspects of contribution. Please follow these guides.

### Python code
* Follow [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
* Run [pylint](https://pylint.readthedocs.io/) over the code and resolve any issues appropriately

### Git commit messages
* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Documentation
* Use [Markdown](https://daringfireball.net/projects/markdown/)
