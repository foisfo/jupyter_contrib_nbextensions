# -*- coding: utf-8 -*-
"""
This preprocessor removes lines in code cells that have been marked as `folded`
by the codefolding extension
"""

from nbconvert.preprocessors import Preprocessor


class CodeFoldingPreprocessor(Preprocessor):
    """
    :mod:`nbconvert` Preprocessor for the code_folding nbextension.

    Folds codecells as displayed in the notebook.

    The preprocessor is installed by default. To enable codefolding with
    NbConvert, you need to set the configuration parameter
    `NbConvertApp.codefolding=True`.
    This can be done either in the `jupyter_nbconvert_config.py` file::

        c.NbConvertApp.codefolding = True

    or using a command line parameter when calling NbConvert::

        $ jupyter nbconvert --to html --NbConvertApp.codefolding=True mynotebook.ipynb

    """  # noqa: E501

    fold_mark = u'↔'

    def fold_cell(self, cell, folded):
        """
        Remove folded lines and add a '<->' at the parent line
        """
        self.log.debug("CodeFoldingPreprocessor:: folding at: %s" % folded)
        lines = cell.splitlines(True)
        if not lines:
            # no lines -> return
            return cell
        if folded[0] == 0 and lines[0].startswith(('#','%')):
            # fold whole cell when first line is a comment or magic
            self.log.debug("fold whole cell")
            return lines[0].rstrip('\n') + self.fold_mark + '\n'

        foldIndent = 0
        fold = False
        fcell = ""
        isSkipLine = False
        skipped = ""

        for i, line in enumerate(lines):
            # fold indent level
            lstrip = line.lstrip(r' \t')  # strip tabs and spaces
            indent = len(line) - len(lstrip)
            # is it a comment or an empty line
            isSkipLine = not lstrip or lstrip == "\n" or lstrip.startswith("#")

            if indent <= foldIndent and not isSkipLine:
                # folding finished, when we reached no skip line on an upper
                # level
                fold = False
                fcell += skipped  # add back all skipped lines
                skipped = ""

            if not fold:
                # append the line
                if i in folded:
                    fold = True
                    foldIndent = indent
                    fcell += line.rstrip('\n') + self.fold_mark + '\n'
                else:
                    fcell += line
            else:
                # dont append the line
                # when folding we track all continuous skip lines
                # to add them back when we leave this scope
                if not isSkipLine:
                    skipped = ""
                else:
                    skipped += line

            self.log.debug("%02i, %02i < %02i, %i,'%s' ", i, indent,
                           foldIndent, fold, line[0:indent+10].strip("\r\n"))

        return fcell

    def preprocess_cell(self, cell, resources, index):
        """
        Read cell metadata and remove lines marked as `folded`.
        Requires configuration parameter 'NbConvertApp.codefolding = True'

        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        index : int
            Index of the cell being processed (see base.py)
        """
        dofolding = self.config.NbConvertApp.get('codefolding', False) is True
        if hasattr(cell, 'source') and cell.cell_type == 'code' and dofolding:
            if hasattr(cell['metadata'], 'code_folding'):
                folded = cell['metadata']['code_folding']
                if len(folded) > 0:
                    cell.source = self.fold_cell(cell.source, folded)
        return cell, resources
