"""DfManipulator class
"""

import pandas as pd
import numpy as np

RESERVED_COLUMNS = {'func_result', 'max_depth', 'dropna', 'transformer'}


class Transformer:
    """class to transform wide dataframes pulled from datajoint
    """

    def __init__(
        self, df,
        datacols=None, indexcols=None,
        inplace=True
    ):
        assert isinstance(df, pd.DataFrame), "df must be a pandas DataFrame."

        truth = RESERVED_COLUMNS & set(df.columns)
        assert not truth, (
            f'dataframe has columns that are reserved: {truth}.'
        )

        if datacols is None and indexcols is None:
            # indexcols already in index
            pass
        else:
            if indexcols is None:
                indexcols = list(set(df.columns) - set(datacols))
            elif datacols is None:
                datacols = list(set(df.columns) - set(indexcols))

            # no columns given that are not in dataframe
            truth = set(datacols) - set(df.columns)
            assert not truth, (
                f'datacols contains columns not in dataframe: {truth}.'
            )
            truth = set(indexcols) - set(df.columns)
            assert not truth, (
                f'indexcols contains columns not in dataframe: {truth}.'
            )
            # keep original index for uniqueness
            if inplace:
                df.set_index(indexcols, append=True, inplace=True)
            else:
                df = df.set_index(indexcols, append=True)

            # if only a few columns were selected
            if set(df.columns) - set(datacols):
                df = df[datacols]

        assert isinstance(df.index, pd.MultiIndex), (
            "df index must be multiindex"
        )
        truth = all(
            str(col).isidentifier() for col in df.columns
        ) + all(
            str(name).isidentifier() for name in df.index.names
        )
        assert truth, (
            "all index names and column names must be string identifiers."
        )
        truth = any(
            str(name).startswith(str(col))
            for name in df.index.names
            for col in df.columns
        )
        assert not truth, (
            "not any index names can startwith the same name as column names."
        )

        if inplace:
            self._df = df
        else:
            self._df = df.copy()

        # stringify everything
        self._df.rename(
            columns={col: str(col) for col in self._df.columns},
            inplace=True
        )
        self._df.index.set_names(
            [str(name) for name in self._df.index.names],
            inplace=True
        )

    @property
    def df(self):
        return self._df

    def tolong(
        self, transformer=iter, max_depth=3, dropna=True,
        **shared_axes
    ):
        """
        """

        truth = all(
            (
                # key must be unique
                all(not key.startswith(col) for col in self._df.columns)
                and key not in self._df.index.names
                # must be dictionary
                and isinstance(shared, dict)
                # keys must be in columns
                and not (set(shared) - set(self._df.columns))
            )
            for key, shared in shared_axes.items()
        )
        assert truth, (
            'shared axes arguments must be dictionaries '
            'with keys corresponding to columns and '
            'values corresponding to axes. '
            'The keyword will correspond to the new column name; '
            'it must be unique and not start the same way as any '
            'column in the dataframe.'
        )

        # iterate of each data column
        for m, (label, series) in enumerate(self._df.items()):
            # set first depth
            n = 0
            # if series already not object skip
            while series.dtype == object and max_depth > n:
                series = self._superstack_series(
                    series, label, transformer, dropna,
                    self._get_col_name(label, n, shared_axes)
                )
                n += 1

            # TODO check if most efficient solution
            # convert series to frame
            names = set(series.index.names)
            _df = series.reset_index()
            #
            if not m:
                df = _df
            else:
                on = list(names & set(df.columns))
                df = pd.merge(df, _df, on=on, how='outer')

        return df

    @staticmethod
    def _get_col_name(label, n, shared_axes):
        # if it is a shared axes the column name is key
        # else it is "label_n"
        for key, shared in shared_axes.items():
            if shared.get(label, None) == n:
                return key
        return f"{label}_{n}"

    @staticmethod
    def _superstack_series(series, label, transformer, dropna, col_name):
        # apply series transformer (iter is default for sequences)
        # series.index is already assumed to be multi index
        # transform into dataframe
        # this should automatically infer types
        df = series.apply(
            lambda x: pd.Series(transformer(x)),
            convert_dtype=True
        )
        # give columns index a name
        df.columns.name = col_name
        # stack dataframe
        series = df.stack(dropna=dropna)
        series.name = label
        return series

    def mapfunc(self, func, column, new_col_name=None, **kwargs):
        if new_col_name is None:
            new_col_name = column
        self._df[new_col_name] = self._df[column].apply(func, **kwargs)
        return self

    def applyfunc(self, func, new_col_name, *args, **kwargs):
        if new_col_name is None:
            new_col_name = 'func_result'
        self._df[new_col_name] = self._df.apply(
            lambda x: func(
                *(x[arg] for arg in args),
                **{key: x[arg] for key, arg in kwargs.items()}
            ),
            axis=1, result_type='reduce'
        )
        return self

    def drop(self, *columns):
        self._df.drop(
            columns=columns,
            inplace=True
        )
        return self
