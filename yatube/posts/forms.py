from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'post text',
            'group': 'group title',
            'image': 'image',
        }

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'author')
        help_texts = {
            'text': 'Comment text',
        }
