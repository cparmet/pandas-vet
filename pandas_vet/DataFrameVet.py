from .options import _initialize_format_options
from .run_checks import _check_data, _modify_data
from .timer import print_time_elapsed, start_timer
from .utils import _filter_emojis, _format_fail_message, _format_success_message, _lambda_to_string
import matplotlib.pyplot as plt
import pandas as pd
from pandas.core.groupby.groupby import DataError


## Public methods added to Pandas DataFrame
@pd.api.extensions.register_dataframe_accessor("check")
class DataFrameVet:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def set_format(self, **kwargs):
        for arg, value in kwargs.items():
            vet_option = arg if arg.startswith("vet.") else "vet." + arg # Fully qualified
            if vet_option in pd._config.config._select_options("vet"):
                pd.set_option(vet_option, value)
            else:
                raise AttributeError(f"No Pandas Vet option for {vet_option}. Available options: {pd._config.config._select_options('vet')}")
        return self._obj

    def reset_format(self):
        """Re-initilaize all Pandas Vet options for formatting"""
        _initialize_format_options()
        return self._obj

    def assert_data(
            self,
            condition,
            subset=None,
            exception_class=DataError,
            pass_message=" ✔️ Assertion passed ",
            fail_message=" ㄨ Assertion failed ",
            raise_exception=True,
            verbose=False
            ):
        data = self._obj[subset] if subset else self._obj
        if callable(condition):
            result = condition(data)
            condition_str = _lambda_to_string(condition)
        elif isinstance(condition, str):
            result = eval(condition_str:=condition, {}, {"df": data})
        else:
            raise TypeError(f"Argument `condition` is of unexpected type {type(condition)}")
        if not result:
            if raise_exception:
                raise exception_class(f"{fail_message}: {condition_str}") 
            else:
                print(f"{_format_fail_message(fail_message)}: {condition_str}")
        if verbose:
            print(f"{_format_success_message(pass_message)}: {condition_str}")
        return self._obj

    def describe(self, fn=lambda df: df, subset=None, check_name='📏 Distributions',**kwargs):
        _check_data(
            self._obj,
            check_fn=lambda df: df.describe(**kwargs),
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj

    def columns(self, fn=lambda df: df, subset=None, check_name='🏛️ Columns'):
        _check_data(
            self._obj,
            check_fn=lambda df: df.columns.tolist(),
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj

    def dtypes(self, fn=lambda df: df, subset=None, check_name='🗂️ Data types'):
        _check_data(
            self._obj,
            check_fn=lambda df: df.dtypes,
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj

    def evaluate(self, fn=lambda df: df, subset=None, check_name=None):
        _check_data(
            self._obj,
            modify_fn=fn,
            subset=subset,
            check_name=check_name)
        return self._obj
    
    def head(self, n=5, fn=lambda df: df, subset=None, check_name=None):
        _check_data(
            self._obj,
            check_fn=lambda df: df.head(n),
            modify_fn=fn,
            subset=subset,
            check_name=check_name if check_name else f"⬆️ First {n} rows"
            )
        return self._obj

    def hist(self, fn=lambda df: df, subset=[], check_name=None, **kwargs):
        _ = (
            _modify_data(self._obj, fn, subset)
            .hist(**kwargs)
            )
        _ = plt.suptitle(
            check_name if check_name else "Distribution" if len(subset)==1 else "Distributions"
            )

        return self._obj

    def info(self, fn=lambda df: df, subset=None, check_name='ℹ️ Info', **kwargs):
        """Don't use display or check_name comes below report """
        print()
        print(_filter_emojis(check_name))
        (
            _modify_data(self._obj, fn, subset)
            .info(**kwargs)
        )
        return self._obj
    
    def memory_usage(self, fn=lambda df:df, subset=None, check_name='💾 Memory usage', **kwargs):
        _check_data(
            self._obj,
            check_fn=lambda df: df.memory_usage(**kwargs),
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj
        
    def ncols(self, fn=lambda df: df, subset=None, check_name='🏛️ Columns'):
        _check_data(
            self._obj,
            check_fn=lambda df: df.shape[1],
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj

    def ndups(self, fn=lambda df: df, subset=None, check_name=None, **kwargs):
        """kwargs are arguments to .duplicated() """
        _check_data(
            self._obj,
            check_fn=lambda df: df.duplicated(**kwargs).sum(),
            modify_fn=fn,
            subset=subset,
            check_name=check_name if check_name else f'👯‍♂️ Rows with duplication in {subset}' if subset else '👯‍♂️ Duplicated rows')
        return self._obj

    def nnulls(self, fn=lambda df: df, subset=None, by_column=True, check_name=None):
        """

        by_column = False to count rows that have any NaNs in any columns
        """
        print()
        data = _modify_data(self._obj, fn, subset)
        na_counts = data.isna().any(axis=1).sum() if isinstance(data, pd.DataFrame) and not by_column else data.isna().sum()
        if not check_name:
            if isinstance(na_counts, (pd.DataFrame, pd.Series)): # Report result as a pandas object
                _check_data(na_counts, check_name=f'👻 Rows with NaNs in {subset}' if subset else '👻 Rows with NaNs')
            else: # Report on one line
                print(
                    _filter_emojis(f'👻 Rows with NaNs in {subset}: ' if subset else '👻 Rows with NaNs: ')
                    + f"{na_counts} out of {data.shape[0]}" 
                )  
        else:
            print(f"{_filter_emojis(check_name)}: {na_counts}")
        return self._obj

    def nrows(self, fn=lambda df: df, subset=None, check_name='☰ Rows'):
        _check_data(
            self._obj,
            check_fn=lambda df: df.shape[0],
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj

    def nunique(self, column, fn=lambda df: df, check_name=None, **kwargs):
        _check_data(
            self._obj,
            check_fn=lambda df: df.nunique(**kwargs),
            modify_fn=fn,
            subset=column,
            check_name=check_name if check_name else f"🌟 Unique values in {column}"
            )
        return self._obj

    def plot(self, fn=lambda df: df, subset=None, check_name="", **kwargs):
        """'title' kwarg overrides check_name as plot title"""
        _ = (
            _modify_data(self._obj, fn, subset)
            .plot(
                # Pass along kwargs to Pandas plot() method
                # If user hasn't included "title" in kwargs, use check_name
                **(
                {**kwargs, "title": _filter_emojis(check_name)} if "title" not in kwargs
                else kwargs
                )
                  )
        )
        return self._obj
    
    def print(self, text=None, fn=lambda df: df, subset=None, check_name=None, max_rows=10):
        _check_data(
            text if text else self._obj,
            check_fn=lambda data: data if text else data.head(max_rows),
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj
    
    def shape(self, fn=lambda df: df, subset=None, check_name='📐 Shape'):
        """See nrows, ncols"""
        _check_data(
            self._obj,
            check_fn=lambda df: df.shape,
            modify_fn=fn,
            subset=subset,
            check_name=check_name
            )
        return self._obj

    def start_timer(self, verbose=False):
        start_timer(verbose) # Call the public function
        return self._obj

    def tail(self, n=5, fn=lambda df: df, subset=None, check_name=None):            
        _check_data(
            self._obj,
            check_fn=lambda df: df.tail(n),
            modify_fn=fn,
            subset=subset,
            check_name=check_name if check_name else f"⬇️ Last {n} rows"
            )
        return self._obj
    
    def print_time_elapsed(self, check_name="Time elapsed", units="auto"):
        print_time_elapsed(check_name=check_name, units=units) # Call the public function
        return self._obj

    def unique(self, column, fn=lambda df: df, check_name=None):
        _check_data(
            self._obj,
            check_fn=lambda s: s.unique().tolist(),
            modify_fn=fn,
            subset=column,
            check_name=check_name if check_name else f"🌟 Unique values of {column}"
            )
        return self._obj

    def value_counts(self, column, max_rows=10, fn=lambda df: df, check_name=None, **kwargs):
        _check_data(
            self._obj,
            check_fn=lambda df: df.value_counts(**kwargs).head(max_rows),
            modify_fn=fn,
            subset=column,
            check_name=check_name if check_name else f"🧮 Value counts, first {max_rows} values" if max_rows else f"🧮 Value counts"
            )
        return self._obj

    def write(self, path, fn=lambda df: df, subset=None, verbose=False):
        data = _modify_data(self._obj, fn, subset)
        if path.endswith(".xls") or path.endswith(".xlsx"):
            data.to_excel(path)
        elif path.endswith(".csv"):
            data.to_csv(path)
        elif path.endswith(".parquet"):
            data.to_parquet(path)
        else:
            raise AttributeError(f"Can't write data to file. Unknown file extension in: {path}. ")
        if verbose:
            print(_filter_emojis("📦 Wrote file {path}"))
        return self._obj


# Initialize configuration
_initialize_format_options()