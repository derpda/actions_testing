# Require Python >= 3.7
# -*- coding: utf-8 -*-
"""
# This script parses and validates the release notes for the edge-ocr-models repository.
# It checks for the presence of mandatory sections and subsections, and validates their content.
"""
import re
import sys

if sys.version_info < (3, 7):
    raise Exception("Python 3.7 or higher is required to run this script.")

import argparse
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Optional, Set, Tuple


class SECTION(Enum):
    PRIVATE = "内部リリースノート"
    PUBLIC = "公開リリースノート"

    @staticmethod
    def from_str(string: str) -> "SECTION":
        """
        Convert a string to a SECTION enum.
        """
        for section in SECTION:
            if section.value == string:
                return section
        raise ValueError(f"Unknown section {string}")


class SUBSECTION(Enum):
    Changes = "変更点"
    Companies = "公開先会社"
    CustomType = "カスタムタイプ"
    MinSDK = "最小対応 SDK バージョン"
    MLFlow = "MLFlowリンク"

    @staticmethod
    def from_str(string: str) -> "SUBSECTION":
        """
        Convert a string to a SUBSECTION enum.
        """
        for subsection in __class__:
            if subsection.value == string:
                return subsection
        raise ValueError(f"Unknown subsection {string}")


def parse_mlflow_link(content: str):
    # Expecting either of the following:
    # - http://
    # - https://
    # Check if the first line contains a valid MLFlow link
    if not content:
        raise ValueError("MLFlow section is empty")
    lines = content.split("\n")
    found_link = False
    for line in lines:
        if line.startswith("- https://") or line.startswith("- http://"):
            found_link = True
            break
    if not found_link:
        raise ValueError("MLFlow link is missing or invalid")
    # Check if the link is valid?


def parse_min_sdk_version(content: str):
    # Expected format:
    # - 1.2.3以上
    # Check if the first line contains a valid version number
    if not content:
        raise ValueError("Minimum SDK version section is empty")
    found_version = False
    lines = content.split("\n")
    version_regex = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
    for line in lines:
        if not line.strip().startswith("- "):
            continue
        # Check if the version number is valid
        version = line[2:].strip()
        if not version_regex.match(version):
            raise ValueError(f"Invalid version number {version}")
        found_version = True
        break
    if not found_version:
        raise ValueError("Minimum SDK version is missing or invalid")
    # Check if the version number is valid?


def parse_companies(content: str):
    # Expected format:
    # - 会社名1: 会社ID1
    # - 会社名2: 会社ID2
    if not content:
        raise ValueError("Companies section is empty")
    lines = content.split("\n")
    companies = {}
    for line in lines:
        if not line.strip().startswith("- "):
            continue
        # Check if the company name and ID are valid
        company = line[2:].strip()
        if ":" not in company:
            raise ValueError(f"Invalid company format {company}")
        name, id_ = company.split(":", 1)
        name = name.strip()
        id_ = id_.strip()
        if not name or not id_:
            raise ValueError(f"Invalid company format {company}")
        if id_ in companies:
            raise ValueError(f"Duplicate company ID {id_}")
        companies[id_] = name
    with open("companies.txt", "w") as file:
        for id_, name in companies.items():
            file.write(f"{id_} {name}\n")


def parse_custom_type(content: str):
    # Expected format:
    # - カスタムタイプ名
    if not content:
        raise ValueError("Custom type section is empty")
    lines = content.split("\n")
    custom_type: Optional[str] = None
    for line in lines:
        if not line.strip().startswith("- "):
            continue
        # Check if the custom type name is valid
        content = line[2:].strip()
        if not content:
            raise ValueError("Custom type name is empty")
        custom_type = content
        break
    if custom_type is None:
        raise ValueError("Custom type is missing")
    with open("custom_type.txt", "w") as file:
        file.write(custom_type)


SUBSECTION_VALIDATORS: Dict[SUBSECTION, Callable[[str], None]] = {
    SUBSECTION.MLFlow: parse_mlflow_link,
    SUBSECTION.MinSDK: parse_min_sdk_version,
    SUBSECTION.Companies: parse_companies,
    SUBSECTION.CustomType: parse_custom_type,
}


class Level(Enum):
    SECTION = 2
    SUBSECTION = 3


def to_md(section: str, level: Level) -> str:
    """
    Convert a section name to markdown format.
    """
    if level == Level.SECTION:
        return f"## {section}\n"
    elif level == Level.SUBSECTION:
        return f"### {section}\n"
    else:
        raise ValueError("Invalid level")


def from_md(section: str) -> str:
    """
    Convert a section name from markdown format.
    """
    if section.startswith("## "):
        return section.strip()[3:]
    elif section.startswith("### "):
        return section.strip()[4:]
    else:
        raise ValueError("Invalid markdown format")


class ReleaseType(Enum):
    Model = "model"
    SDK = "sdk"

    @staticmethod
    def from_str(string: str) -> "ReleaseType":
        """
        Convert a string to a ReleaseType enum.
        """
        for release_type in ReleaseType:
            if release_type.value == string:
                return release_type
        raise ValueError(f"Unknown release type {string}")


class ReleaseNotesParser:
    def __init__(self):
        # NOTE: We rely on dict being ordered to maintain the order of sections
        # in the release notes. Thus, require Python 3.7 or higher.
        self.sections: Dict[SECTION, Tuple[str, Dict[str, str]]] = {}

    def parse(self, lines: str):
        # First, split into sections
        sections = lines.lstrip().split("\n## ")
        if not sections[0].startswith("## "):
            raise ValueError("Release notes must start with a section (see README.md)")
        # Add the newline back in
        # sections[0] += "\n"
        # Fix the first section name
        section_lines = sections[0].split("\n")
        section_lines[0] = from_md(section_lines[0])
        sections[0] = "\n".join(section_lines)
        for section in sections:
            section_name, content = section.split("\n", maxsplit=1)
            section_name = SECTION.from_str(section_name)
            # Split into subsections
            subsections = content.split("\n### ")
            # Add the newlines back in
            for i in range(len(subsections) - 1):
                subsections[i] += "\n"
            if subsections[0].startswith("### "):
                subsection_lines = subsections[0].split("\n")
                subsection_lines[0] = from_md(subsection_lines[0])
                subsections[0] = "\n".join(subsection_lines)
                raw_section_content = ""
            else:
                raw_section_content = subsections[0]
                subsections = subsections[1:]
            subsections_dir = {}
            for subsection in subsections:
                subsection_name, subcontent = subsection.split("\n", maxsplit=1)
                subsections_dir[subsection_name] = subcontent
            # Add the section to the sections dict
            self.sections[section_name] = (raw_section_content, subsections_dir)

    def get_section_text(self, section: SECTION) -> str:
        """
        Get the printable content of a section.
        """
        if section not in self.sections.keys():
            raise ValueError(f"Section {section} is missing")
        full_content = self.sections[section][0]
        for subsection in self.sections[section][1]:
            full_content += to_md(subsection, Level.SUBSECTION)
            full_content += self.sections[section][1][subsection]
        # Always add a newline at the end
        if not full_content.endswith("\n"):
            full_content += "\n"
        return full_content

    def validate(self, release_type: ReleaseType):
        expected_sections: Dict[SECTION, Set[SUBSECTION]] = {}
        if release_type == ReleaseType.Model:
            limited_release = False
            if SECTION.PUBLIC not in self.sections.keys():
                limited_release = True
            if limited_release:
                expected_sections[SECTION.PRIVATE] = {
                    SUBSECTION.MLFlow,
                    SUBSECTION.MinSDK,
                    SUBSECTION.Companies,
                    SUBSECTION.CustomType,
                }
            else:
                expected_sections[SECTION.PRIVATE] = {SUBSECTION.MLFlow}
                expected_sections[SECTION.PUBLIC] = {
                    SUBSECTION.Changes,
                    SUBSECTION.MinSDK,
                }
        elif release_type == ReleaseType.SDK:
            expected_sections[SECTION.PUBLIC] = {SUBSECTION.Changes}
        else:
            raise ValueError(f"Unknown release type {release_type}")
        # Check that all mandatory sections are present
        for section, subsections in expected_sections.items():
            if section not in self.sections.keys():
                raise ValueError(f"Section {SECTION.PRIVATE} is missing")
            for subsection in subsections:
                if subsection.value not in self.sections[section][1].keys():
                    raise ValueError(
                        f'Mandat ory subsection "{subsection.value}" is missing in {section}'
                    )
                if subsection in SUBSECTION_VALIDATORS:
                    SUBSECTION_VALIDATORS[subsection](
                        self.sections[section][1][subsection.value]
                    )
        if SECTION.PUBLIC in self.sections:
            with open("public.md", "w") as file:
                file.write(self.get_section_text(SECTION.PUBLIC))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release_notes", type=str, help="Markdown file containing the release notes"
    )
    parser.add_argument(
        "--release_type",
        type=str,
        choices=[e.value for e in ReleaseType],
        help="Type of release",
    )
    args = parser.parse_args()

    release_notes_path = Path(args.release_notes)
    if not release_notes_path.exists():
        print(f"Release notes file {release_notes_path} does not exist")
        exit(1)

    # Create the parser
    parser = ReleaseNotesParser()

    print(f"Checking release notes in {release_notes_path}")
    with open(release_notes_path, "r") as file:
        content = file.read()
    if len(content) == 0:
        print("Release notes file is empty")
        exit(1)

    parser.parse(content)
    parser.validate(ReleaseType.from_str(args.release_type))
    print("Release notes are valid")


if __name__ == "__main__":
    main()
