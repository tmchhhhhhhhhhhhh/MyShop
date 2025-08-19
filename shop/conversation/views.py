from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Max

from .models import Item, Conversation
from .forms import ConversationMessageForm


@login_required
def new_conversation(request, item_pk):
    item = get_object_or_404(Item, pk=item_pk)

    # Нельзя писать самому себе
    if item.created_by_id == request.user.id:
        return redirect("dashboard:index")

    # Ищем существующий разговор между текущим пользователем и владельцем товара по этому item
    conversation = (
        Conversation.objects.filter(item=item)
        .filter(members=request.user)
        .filter(members=item.created_by)  # второй фильтр по M2M -> оба участника
        .first()
    )

    if request.method == "POST":
        form = ConversationMessageForm(request.POST)
        if form.is_valid():
            if conversation is None:
                conversation = Conversation.objects.create(item=item)
                conversation.members.add(request.user, item.created_by)

            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # Лучше вести в детальную переписку
            return redirect("conversation:detail", pk=conversation.pk)
    else:
        # Если разговор уже есть — сразу ведём в него
        if conversation is not None:
            return redirect("conversation:detail", pk=conversation.pk)
        form = ConversationMessageForm()

    return render(
        request,
        "conversation/new.html",
        {"item": item, "form": form},
    )


@login_required
def inbox(request):
    latest_ids_per_item = (
        Conversation.objects.filter(members=request.user)
        .values("item")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )

    conversations = (
        Conversation.objects.filter(id__in=latest_ids_per_item)
        .select_related("item")
        .prefetch_related("members")
        .order_by("-updated_at")
    )

    return render(
        request,
        "conversation/inbox.html",
        {"conversations": conversations},
    )


@login_required
def detail(request, pk):
    conversation = Conversation.objects.filter(members__in=[request.user]).get(pk=pk)

    # Проверяем, что текущий пользователь является участником разговора
    if request.user not in conversation.members.all():
        return redirect("conversation:inbox")

    if request.method == "POST":
        form = ConversationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            conversation.save()
            return redirect("conversation:detail", pk=pk)
    else:
        form = ConversationMessageForm()

    return render(
        request,
        "conversation/detail.html",
        {"conversation": conversation, "form": form},
    )
