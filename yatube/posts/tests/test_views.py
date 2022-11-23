from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TOTAL_POSTS: int = 20
POSTS_AUTHOR_USER: int = 13
POSTS_WITH_GROUP: int = 17
POST_IN_PAGE: int = 10


class PostVievsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Создается 2 обьекта юзер, 20 постов,
        # 13 с одним автором и 7 со вторым, 17 с одной группой
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_another = User.objects.create_user(username='I_is_not_NoName')
        cls.group = Group.objects.create(
            title='test-text',
            slug='test-slug',
            description='test_description',
        )
        for i in range(3):
            cls.post = Post.objects.create(
                author=cls.user_another,
                text='test-post-text',)
        for i in range(4):
            cls.post = Post.objects.create(
                author=cls.user_another,
                text='test-post-text',
                group=cls.group)
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='test-post-text',
                group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон списков сформирован с правильным контекстом."""
        pages_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'NoName'}),
        }
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                self.assertEqual(post_author_0, 'NoName')
                self.assertEqual(post_text_0, 'test-post-text')

    def test_first_page_contains_ten_records(self):
        '''Тест паджинатора'''
        pages_names = {
            reverse('posts:index'): TOTAL_POSTS,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): POSTS_WITH_GROUP,
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}): POSTS_AUTHOR_USER,
        }
        for reverse_name in pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 POST_IN_PAGE)
        for reverse_name, post_count in pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 post_count - POST_IN_PAGE)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id})))
        self.assertEqual(response.context.get('post_more').author.username,
                         'NoName')
        self.assertEqual(response.context.get('post_more').text,
                         'test-post-text')
        self.assertEqual(response.context.get('post_more').group.title,
                         'test-text')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create и edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_show_correct_group(self):
        """ post при создании с группой отображается на всех страницах
            и не попадает в другую группу."""
        self.new_group = Group.objects.create(
            title='new',
            slug='new-test-slug',
            description='new-test_description',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='new-test-post-text',
            group=self.new_group,)
        checks = {reverse('posts:index'),
                  reverse('posts:group_list',
                          kwargs={'slug': 'new-test-slug'}),
                  reverse('posts:profile', kwargs={'username': 'NoName'}),
                  }
        for reverse_name in checks:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                self.assertEqual(post_author_0, 'NoName')
                self.assertEqual(post_text_0, 'new-test-post-text')
                self.assertEqual(post_group_0, 'new')
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        self.assertEqual(post_text_0, 'test-post-text')
        self.assertEqual(post_group_0, 'test-text')
