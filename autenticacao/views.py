import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth, messages
from django.contrib.messages import constants
from django.conf import settings

from .utils import password_is_valid, email_html
from .models import Ativacao


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "GET":
        return render(request, 'cadastro.html')
    elif request.method == "POST":
        username = request.POST.get('usuario')
        senha = request.POST.get('senha')
        email = request.POST.get('email')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not password_is_valid(request, senha, confirmar_senha):
            return redirect('/auth/cadastro')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=senha,
                is_active=False,
            )
            user.save()

            token = os.urandom(16).hex()
            ativacao = Ativacao(token=token, user=user)
            ativacao.save()

            path_template = os.path.join(
                settings.BASE_DIR,
                'autenticacao/templates/emails/cadastro_confirmado.html',
            )
            email_html(
                path_template,
                'Cadastro confirmado',
                [email],
                username=username,
                link_ativacao=f"127.0.0.1:8000/auth/ativar_conta/{token}",
            )

            messages.add_message(request, constants.SUCCESS, 'Usuário cadastrado com sucesso! Verifique seu e-mail.')
            return redirect('/auth/logar')
        except:
            messages.add_message(request, constants.ERROR, 'Erro interno do sistema')
            return redirect('/auth/cadastro')


def logar(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == "GET":
        return render(request, 'logar.html')
    elif request.method == "POST":
        username = request.POST.get('usuario')
        senha = request.POST.get('senha')

        usuario = auth.authenticate(username=username, password=senha)

        if not usuario:
            messages.add_message(request, constants.ERROR, 'Username ou senha inválidos')
            return redirect('/auth/logar')
        else:
            auth.login(request, usuario)
            return redirect('/pacientes/')


def sair(request):
    auth.logout(request)
    return redirect('/auth/logar')


def ativar_conta(request, token):
    token = get_object_or_404(Ativacao, token=token)
    if token.ativo:
        messages.add_message(request, constants.WARNING, 'Essa token já foi usado')
        return redirect('/auth/logar')
    user = User.objects.get(username=token.user.username)
    user.is_active = True
    user.save()
    token.ativo = True
    token.save()
    messages.add_message(request, constants.SUCCESS, 'Conta ativa com sucesso')
    return redirect('/auth/logar')
