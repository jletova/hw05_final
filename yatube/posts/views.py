from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (
    render, redirect, get_object_or_404)

from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm

from .models import Follow, Post, Group, User, Comment


namespace = 'posts'


def paginate(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    context = {
        'page_obj': paginate(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginate(request, post_list),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    following = False
    if request.user.is_authenticated and request.user != author:
        following = Follow.objects.filter(
            user=request.user, author__username=username
            ).exists()
    context = {
        'author': author,
        'page_obj': paginate(request, post_list),
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'form': CommentForm(request.POST),
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        author = request.user
        form = PostForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = author
            new_post.save()
            return redirect('posts:profile', author)
        return render(request, template, {'form': form})
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginate(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user, author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username
    ).delete()
    return redirect('posts:profile', username)
