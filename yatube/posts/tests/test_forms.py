from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from http import HTTPStatus

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='test-text',
            slug='test-slug',
            description='test_description',)
        cls.post = Post.objects.create(
            author=cls.user,
            text='test-post-text',
            group=cls.group)       
        cls.form = PostForm()         

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)    
           
    def test_post_create(self):
        """создает запись в Post."""
        post_count = Post.objects.count()  
    
        form_data = {
            'text': '',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(
            response, 
            'form',
            'text',
            'Обязательное поле.'
        )
        form_data = {
            'text': 'New-test-text',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Изменяет запись в Post.""" 
        form_data_1 = {
            'text': 'New-text',
            'group': self.group.pk
        }
        post_count = Post.objects.count()  
        ##response = self.authorized_client.get(reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        ##form_data['text']='newe'
        #form_data = {
        #    'text': 'NotNew-test-text',
        #}
        
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data_1,
            follow=True
        )
        post_edit = Post.objects.get(pk=self.post.id)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, 'New-text')
