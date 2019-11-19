# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0]
### Added
- Additional documentation: CHANGELOG.md, and CONTRIBUTING.md
- Pretrain folder containing a pretrained pkl file
- New models in model folder

### Changed
- Copyright holder in LICENSE file
- Removed installation of python 3.6 in Docker images and installation of dependencies via the requirements.txt file
- README file with the newly implemented models and installation via Docker
- Available datasets in dataset folder

### Removed
- Evaluation folder with relevant files

### Fixed
- DiffNet model with missing social_file property and incorrect train matrix variable name
- NGCF model by correcting the merging of two arrays
- SASRec model by correcting name of required build_graph() function