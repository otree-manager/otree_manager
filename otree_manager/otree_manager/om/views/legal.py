from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth.decorators import login_required

"""Views for editing legal pages."""

# While there is some code duplication here, this is intentional 
# to keep flexibility for future changes to these parts of the app
# consider this temporary.

@login_required
def imprint_edit(request):
    """Imprint and contact information page"""
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    page_model = FlatPage.objects.get(url='/legal/imprint/')

    if request.method == 'POST':
        form = FlatpageForm(request.POST or None, instance=page_model)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('imprint'))
    else:
        form = FlatpageForm(instance=page_model)

    return render(request, 'om/legal/edit_imprint.html', {'form': form})


@login_required
def privacy_edit(request):
    """Privacy statements page"""
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    page_model = FlatPage.objects.get(url='/legal/privacy/')

    if request.method == 'POST':
        form = FlatpageForm(request.POST or None, instance=page_model)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('privacy'))
    else:
        form = FlatpageForm(instance=page_model)

    return render(request, 'om/legal/edit_privacy.html', {'form': form})