from django import forms
from ..models.blocks import AgentBlockSettings


class AgentBlocksForm(forms.ModelForm):
    """Форма для керування порядком блоків"""

    class Meta:
        model = AgentBlockSettings
        fields = ['blocks_order', 'active_blocks', 'custom_css', 'custom_js']