# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_class_confusion.ipynb (unless otherwise specified).

__all__ = ['ClassConfusion']

# Cell
from fastai2.tabular.data import TabDataLoader
from fastai2.data.transforms import TfmdDL
from fastcore.dispatch import typedispatch, patch
import matplotlib

# Cell
#export
try:
    from google.colab import widgets
except ImportError:
    raise ImportError('Requires to be run in Google Colaboratory')
from tqdm import tqdm

# Cell
#export
@typedispatch
def _get_names(x:TabDataLoader, idxs, mc=None, varlist=None, li=None):
    "Creates names for the tabs"
    boxes = len(idxs)
    cols = math.ceil(math.sqrt(boxes))
    rows = math.ceil(boxes/cols)
    tbnames = x.cat_names.filter(lambda x: '_na' not in x) + x.cont_names if varlist is None else varlist
    tbnames = list(tbnames)
    return [tbnames, boxes, cols, rows, None]

# Cell
#export
@typedispatch
def _get_names(x:TfmdDL, idxs, mc=None, varlist=None, li=None):
    ranges = []
    tbnames = []
    boxes = int(input('Please enter a value for `k`, or the top # images you will see: \n'))
    for x in iter(mc):
        for y in range(len(li)):
            if x[0:2] == li[y]:
                ranges.append(x[2])
                tbnames.append(f'{x[0]} | {x[1]}')
    return [tbnames, boxes, None, None, ranges]

# Cell
#export
@patch
def get_losses(x:TabDataLoader, tl_idx, preds, combs):
    "Gets losses from `TabDataLoader`"
    df_list = []
    preds = preds.argmax(dim=1)
    dset = x.dataset
    dset.decode()
    df_list.append(dset.all_cols)
    for c in combs:
        idxs = []
        for i, idx in enumerate(tl_idx):
            if x.vocab[preds[idx]] == c[0] and dset.ys.iloc[int(idx)].values == c[1]:
                idxs.append(int(idx))
        df_list.append(dset.all_cols.iloc[idxs])
    dset.process()
    return df_list

# Cell
#export
@patch
def get_losses(x:TfmdDL, tl_idx, preds, combs):
    "Get losses and original `x` from `DataLoaders`"
    groupings = []
    preds = preds.argmax(dim=1)
    dset = x.dataset
    dec = [x.vocab[i] for i in preds]
    for c in combs:
        idxs = []
        for i, idx in enumerate(tl_idx):
            if dec[idx] == c[0] and dset.vocab[dset[int(i)][1]] == c[1]:
                idxs.append(int(idx))
        groupings.append(idxs)
    return groupings

# Cell
@typedispatch
def _plot(x:TfmdDL, interp, idxs, combs, tab, i=None, boxes=None, cols=None, rows=None, ranges=None, figsize=(12,12), cut_off=100):
    "Plot top pictures per classes chosen"
    y = 0
    if ranges[i] < boxes:
        cols = math.ceil(math.sqrt(ranges[i]))
        rows = math.ceil(ranges[i]/cols)
    if ranges[i]<4 or boxes < 4:
        cols, rows = 2, 2
    else:
        cols = math.ceil(math.sqrt(boxes))
        rows = math.ceil(boxes/cols)
    fig, ax = plt.subplots(rows, cols, figsize=figsize)
    [axi.set_axis_off() for axi in ax.ravel()]
    for j, idx in enumerate(idxs[i]):
        if boxes < y+1 or y > ranges[i]: break
        row = (int)(y/cols)
        col = y % cols
        img, lbl = x.dataset[idx]
        fn = x.items[idx]
        fn = re.search('([^\/]\d+.*$)', str(fn)).group(0)
        img.show(ctx=ax[row,col], title=fn)
        y+=1
    plt.show(fig)
    plt.tight_layout()

# Cell
@typedispatch
def _plot(x:TabDataLoader, interp, idxs, combs, tab, i=None, boxes=None, cols=None, rows=None, ranges=None, figsize=(12,12), cut_off=100):
    "Plot tabular graphs"
    if boxes is not None:
        fig, ax = plt.subplots(boxes, figsize=figsize)
    else:
        fig, ax = plot.subplots(cols, rows, figsize=figsize)
    fig.subplots_adjust(hspace=.5)
    titles = ['Original'] + combs
    for j, y in enumerate(idxs):
        title = f'{titles[j]} {tab} distribution'
        if boxes is None:
            row = int(j/cols)
            col = j%row
        if tab in x.cat_names:
            vals = pd.value_counts(y[tab].values)
            if boxes is not None:
                if vals.nunique() < 10:
                    fig = vals.plot(kind='bar', title=title, ax=ax[j], rot=0, width=.75)
                elif vals.nunique() > cut_off:
                    print(f'Number of unique values ({vals.nunique()}) is above {cut_off}')
                else:
                    fig = vals.plot(kind='barh', title=title, ax=ax[j], width=.75)
            else:
                fig = vals.plot(kind='barh', title=title, ax=ax[row,col], width=.75)
        else:
            vals = y[tab]
            if boxes is not None:
                fig = vals.plot(kind='hist', ax=ax[j], title=title, y='Frequency')
            else:
                fig = vals.plot(kind='hist', ax=ax[row+1, col], title=title, y='Frequency')
            fig.set_ylabel('Frequency')
            if len(set(vals)) > 1:
                vals.plot(kind='kde', ax=fig, title=title, secondary_y=True)
            else:
                print("Less than two unique values, cannot graph the KDE")

# Cell
#export
class ClassConfusion():
    "Plots the most confused datapoints and statistics for model misses. First is prediction second is actual"
    def __init__(self, learn, dl=None, cut_off=100, is_ordered=False, classlist=[],
                varlist=None, figsize=(12,12), **kwargs):
        dl = learn.dls[1] if dl is None else dl
        interp = ClassificationInterpretation.from_learner(learn, dl=dl)
        combs = classlist if is_ordered else list(itertools.permutations(classlist, 2))
        figsize = figsize
        cut_off = cut_off
        vocab = interp.vocab
        _, tl_idx = interp.top_losses(len(interp.losses))
        idxs = dl.get_losses(tl_idx, interp.preds, combs)
        mc = interp.most_confused()
        tbnames, boxes, cols, rows, ranges = self._get_names(x=dl, idxs=idxs, mc=mc, varlist=varlist, li=combs)
        tb = widgets.TabBar(tbnames)
        self._create_tabs(tb, tbnames, dl, interp, idxs, combs, boxes, cols, rows, ranges, figsize, cut_off)

    def _create_tabs(self, tb, tbnames, dl, interp, idxs, combs, boxes, cols, rows, ranges, figsize, cut_off):
        "Adds relevant graphs to each tab"
        with tqdm(total=len(tbnames)) as pbar:
            for i, tab in enumerate(tbnames):
                with tb.output_to(i):
                    _plot(dl, interp, idxs, combs, tab, i, boxes, cols, rows, ranges, figsize, cut_off)
                pbar.update(1)

    def _get_names(self, x, idxs, mc, varlist, li):
        return _get_names(x, idxs, mc, varlist, li)