import pypandoc
import glob
import os
import re


def convertMarkdownDocsToRst():
    pypandoc.ensure_pandoc_installed()

    # TODO make various edits to improve conversion, like removing the Table of Contents
    print("Converting all .md files to .rst...")
    input_dir = '../../doc'
    output_dir = 'generated_docs'
    subdirs = ['', 'how_tos', 'explanations']
    for subdir in subdirs:
        # print(f'>>>> {subdir}')
        input_sub_dir = f'{input_dir}/{subdir}'
        if not os.path.isdir(input_sub_dir):
            print(f'Directory {input_sub_dir} does not exist. Skipping)')
        output_sub_dir = f'{output_dir}/{subdir}'
        convert_all_markdown_files_in_dir(subdir, input_sub_dir, output_sub_dir)


def convert_all_markdown_files_in_dir(subdir, input_sub_dir, output_sub_dir):
    base_names_to_skip = ['README', 'TemplatePage']
    md_files = glob.glob(f'{input_sub_dir}/*.md')
    if not md_files:
        return
    if not os.path.isdir(output_sub_dir):
        os.makedirs(output_sub_dir)
    for file in md_files:
        file_base_file = os.path.split(file)[1]
        file_base_name = os.path.splitext(file_base_file)[0]

        if file_base_name in base_names_to_skip:
            continue
        # print(file_base_name, input_sub_dir, output_sub_dir)
        convert_markdown_to_restructured_text(subdir, file_base_name, input_sub_dir, output_sub_dir)


def convert_markdown_to_restructured_text(subdir, file_base_name, input_dir, output_dir):
    with open(f'{input_dir}/{file_base_name}.md') as markdown_file:
        content = markdown_file.read()

        content = fix_up_markdown_content(subdir, file_base_name, content)
    output = pypandoc.convert_text(''.join(content), 'rst', format='md',
                                   outputfile=f'{output_dir}/{file_base_name}.rst')


def fix_up_markdown_content(subdir, file_base_name, content):
    # Note: We intentionally do not remove the 'GENERATED FILE' comment,
    # as if anyone edits the derived .rst file, it nicely
    # points to the master file.

    content = fixup_boilerplate_text(content)
    content = fixup_generated_snippets(content)
    content = fixup_code_languages_for_pygments(content)
    content = fixup_markdown_hyperlinks(content, subdir, file_base_name)

    with open(file_base_name + '_hacked.md', 'w') as w:
        w.write(content)

    return content


def fixup_boilerplate_text(content):
    # Remove table of contents
    content = re.sub(r'<!-- toc -->.*<!-- endtoc -->', '', content, count=1, flags=re.DOTALL)

    # Remove 'Back to User Guide'
    back_to_user_guide = (
        '---\n'
        '\n'
        '[Back to User Guide](/doc/README.md#top)\n'
    )
    content = content.replace(back_to_user_guide, '')
    return content


def fixup_generated_snippets(content):
    """
    Adjust the expanded code snippets that were generated
    by mdsnippets, to improve rendering by Sphinx
    """

    # Remove 'snippet source' links from all code snippets
    # TODO Instead of master, use the changeset that this was generated from
    content = re.sub(
        r"<sup><a href='([^']+)' title='File snippet `[^`]+` was extracted from'>snippet source</a> ",
        r"(See [snippet source](https://github.com/approvals/ApprovalTests.cpp/blob/master\1))", content)

    # Remove 'anchor' links from all code snippets
    content = re.sub(
        r"\| <a href='#snippet-[^']+' title='Navigate to start of snippet `[^']+`'>anchor</a></sup>",
        '', content)

    return content


def fixup_code_languages_for_pygments(content):
    # Fix "WARNING: Pygments lexer name 'h' is not known"
    # Todo: find out how to fix this in conf.py - this is a horrible hack!
    content = content.replace(
        '\n```h\n',
        '\n```cpp\n')

    # Fix "WARNING: Pygments lexer name 'txt' is not known"
    # Text files don't need any markup
    content = content.replace(
        '\n```txt\n',
        '\n```\n')
    return content


def fixup_markdown_hyperlinks(content, subdir, file_base_name):
    # [MultipleOutputFilesPerTest](/doc/MultipleOutputFilesPerTest.md#top)
    # [MultipleOutputFilesPerTest](MultipleOutputFilesPerTest.html)

    # content = re.sub(
    #     r".*\.md#top",
    #     r"", content)
    # TODO  This is only correct for links in files that are in the same
    #       level that this file is in.
    #       For example, how_tos/TestContainerContents.html links to
    #       /doc/ToString.md#top - which should be converted to
    #       ../ToString.html - but gets converted to ToString.html
    #       which is then not found.
    # TODO  Convert any links to 'TemplatePage.source.md' to links
    #       on the github site
    # TODO  Also pick up anchors other than '#top', e.g.
    #       'Configuration.md#using-sub-directories-for-approved-files'
    # TODO  Links to non-markdown files should go to the github website, e.g.
    #       [scripts/check_links.sh](/scripts/check_links.sh)
    # TODO  Links to .md files outside of the doc directory, or README
    #       (essentially, thinks that won't be copied in to Sphinx)
    #       should go to github, e.g.
    #       [How To Release](/build/HowToRelease.md#top)
    # TODO  Check that the 'TCR' link on Glossary gets converted correctly - maybe
    #       convert all -- in anchor to -

    # If anchor is #top, remove it
    content = re.sub(
        r"\]\(/doc/(.*).md#top\)",
        r"](\1.html)", content)

    # If anchor is not #top, preserve it
    content = re.sub(
        r"\]\(/doc/([^. #)]*).md#([^. #)]*)\)",
        r"](\1.html#\2)", content)

    # TODO  Print out any remaining lines that contain ](/
    # TODO  Print out a list of all adjusted URLs so that I can test them
    lines = content.splitlines()
    for line in lines:
        if '](/' in line:
            print('>>>', subdir, file_base_name, line)

    return content
