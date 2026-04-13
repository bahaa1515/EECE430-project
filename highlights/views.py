from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import MVPForm, MatchHighlightForm
from .models import MVP, MatchHighlight


@login_required
def highlights_view(request):
    highlight = MatchHighlight.objects.select_related("session").first()
    mvp = MVP.objects.select_related("player", "match", "session").first()
    highlight_form = MatchHighlightForm(instance=highlight)
    mvp_form = MVPForm(instance=mvp)

    if request.method == "POST":
        if not request.user.is_coach():
            raise PermissionDenied

        form_type = request.POST.get("form_type")
        if form_type == "highlight":
            highlight_form = MatchHighlightForm(
                request.POST,
                request.FILES,
                instance=highlight,
            )
            if highlight_form.is_valid():
                saved_highlight = highlight_form.save()
                messages.success(
                    request,
                    f"Highlights updated for {saved_highlight.session.title if saved_highlight.session else saved_highlight.title}.",
                )
                return redirect("highlights")
        elif form_type == "mvp":
            mvp_form = MVPForm(request.POST, instance=mvp)
            if mvp_form.is_valid():
                saved_mvp = mvp_form.save(commit=False)
                if highlight and saved_mvp.session_id and highlight.session_id == saved_mvp.session_id:
                    saved_mvp.match = highlight
                saved_mvp.save()
                messages.success(
                    request,
                    f"MVP updated for {saved_mvp.session.title if saved_mvp.session else saved_mvp.player.name}.",
                )
                return redirect("highlights")

    return render(
        request,
        "highlights/highlights.html",
        {
            "highlight": highlight,
            "mvp": mvp,
            "highlight_form": highlight_form,
            "mvp_form": mvp_form,
            "active": "highlights",
        },
    )
