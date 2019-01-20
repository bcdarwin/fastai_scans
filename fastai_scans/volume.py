import ipyvolume as ipv
from fastai.basics import *
from . import transform

__all__ = ['Volume', 'VolumeSegment', 'VolumeSegmentLbl', 'show_volume']

class Volume(ItemBase):
    def __init__(self, data, idx=None, metadata=None, tfm_params=None):
        self.v = tensor(data)
        self.idx = idx
        self.metadata = metadata
        self.tfm_params = tfm_params if tfm_params is None else tensor(tfm_params)
    
    def __repr__(self): return f'{self.__class__.__name__} {tuple(self.shape)}'
    @property
    def shape(self): return self.v.shape
    @property
    def size(self): return self.shape[-3:]
    @property
    def data(self): return self.v.float()
    
    def apply_tfms(self, tfms, do_resolve=True, **kwargs):
        tfms = sorted(listify(tfms), key=lambda o: o.tfm.order)
        if do_resolve:
            for f in listify(tfms):
                if isinstance(f.tfm, transform.TfmPatch): f.resolve(self.tfm_params)
                else:                                       f.resolve()
        for tfm in tfms: self.v = tfm(self.v, **kwargs)
        return self
    
    def show(self, channel=0, n_slices=4, axes=None, figsize=(10,3), hide_axis=True, slice_info=True, title=True, cmap='magma',
             label=None, metadata=[], **kwargs):
        axes = show_volume(self, channel=channel, n_slices=n_slices, axes=axes, figsize=figsize, hide_axis=hide_axis,
                           slice_info=slice_info, title=title, cmap=cmap, label=label, metadata=metadata, **kwargs)

    def show3d(self, channel=0, controls=False, **kwargs):
        v = self.v[channel] if len(self.v.shape) > 3 else self.v
        ipv.quickvolshow(v, controls=controls, **kwargs)
        ipv.show()
    
class VolumeSegment(Volume):
    @property
    def data(self): return self.v.long()

    def show(self, channel=0, n_slices=4, axes=None, figsize=(10,3), hide_axis=True, slice_info=True, title=True, cmap='magma',
             label=None, metadata=[], **kwargs):
        super().show(channel=channel, n_slices=n_slices, axes=axes, figsize=figsize, hide_axis=hide_axis, slice_info=slice_info,
                     title=title, cmap=cmap, label=label, metadata=metadata, **kwargs)

class VolumeSegmentLbl(VolumeSegment):
    def __init__(self, data, lbl, lbl_str, idx=None, metadata=None):
        super().__init__(data, idx=idx, metadata=metadata)
        self.lbl,self.lbl_str = lbl,lbl_str
    
    def __repr__(self): return f'{self.__class__.__name__} {tuple(self.shape)} label:{self.lbl_str!r}'
    
    @property
    def data(self): return (self.v.long(), self.lbl)
    
    def show(self, channel=0, n_slices=4, axes=None, figsize=(10,3), hide_axis=True, slice_info=True, title=True, cmap='magma',
             label=None, metadata=[], **kwargs):
        if label is None: label = self.lbl_str
        super().show(channel=channel, n_slices=n_slices, axes=axes, figsize=figsize, hide_axis=hide_axis, slice_info=slice_info,
                     title=title, cmap=cmap, label=label, metadata=metadata, **kwargs)
    
def show_volume(volume, channel=0, n_slices=4, axes=None, figsize=(10,3), hide_axis=True, slice_info=True, title=True, cmap='magma',
                label=None, metadata=[], extra=[], alpha=None, label_str='Label', **kwargs):
    vol = to_np(volume.v[channel] if len(volume.v.shape) > 3 else volume.v)
    header = [title+'\n'] if isinstance(title, str) else ['']
    header += ['' if (volume.idx is None) or (not slice_info) else f'{volume.idx} - ']
    header += ['' if label is None else f'{label_str}: {label}']
    if axes is None: fig,axes = plt.subplots(1, n_slices, figsize=figsize)
    else           : n_slices = len(axes)
    slices = np.linspace(0, vol.shape[0]-1, n_slices+2)[1:-1].astype(int)
    for i,ax in zip(slices, axes):
        ax.imshow(vol[i], cmap=cmap, **kwargs)
        if hide_axis: ax.axis('off')
        if title:
            si = f'{header[1]}slice {i}\n' if slice_info else ''
            t = f'{header[0]}{si}{header[2]}'
            for e in extra   : t+= f'\n{e}'
            for e in metadata: t+= f'\n{e}: {volume.metadata[e]}'
            ax.set_title(t.strip())

    plt.tight_layout()
    return axes