#from django.shortcuts import render
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.template import RequestContext
from django.shortcuts import render, render_to_response, redirect
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse

from querystring_parser import parser

from backend import models
from backoffice.forms import AccountForm, AreaForm, IndividualForm,\
    CreateIndividualForm, SurveyForm


@login_required(login_url='login/')
def index(request):
    return redirect('my-surveys')
    #return render(request, 'board.html')


@login_required(login_url='login/')
def register(request):
    return render(request, 'board.html')


@login_required(login_url='login/')
def area_detail(request, area_id=-1):
    area = models.Area.objects.filter(id=area_id).first()
    if not area:
        area = models.Area()
        area.observer = request.user.observer

    if area_id == -1 or request.user.observer in area.observer_set.all():
        if request.POST:
            form = AreaForm(request.POST, instance=area)
            if form.is_valid():
                messages.add_message(request,
                                     messages.SUCCESS,
                                     _('Form is successifully updated'))
                form.save()
                return redirect('area-detail', area_id=form.instance.id)
        else:
            form = AreaForm(instance=area)
        return render_to_response("profile_area.html", {
            "form": form,
        }, RequestContext(request))
    else:
        return redirect(index)


@login_required(login_url='login/')
def individual_detail(request, ind_id=-1):
    individual = models.Individual.objects.filter(id=ind_id).first()
    if not individual:
        individual = models.Individual()
        area_id = request.GET.get("area_id")
        area = models.Area.objects.get(id=area_id)
        individual.area = area
        individual.lat = area.lat
        individual.lon = area.lon

    surveys = sorted(individual.survey_set.all(),
                     key=lambda survey: survey.date,
                     reverse=True)
    surveys = surveys[:8]

    if individual.id:
        if request.user.observer in individual.area.observer_set.all():
            if request.POST:
                form = IndividualForm(request.POST, instance=individual)
                if form.is_valid():
                    messages.add_message(request,
                                         messages.SUCCESS,
                                         _('Form is successifully updated'))
                    form.save()
            else:
                form = IndividualForm(instance=individual)
        else:
            messages.add_message(request,
                                 messages.WARNING,
                                 _('Your are not allowed to see this form'))
            return redirect(index)
    else:
        if request.POST:
            form = CreateIndividualForm(request.POST, instance=individual)
            if form.is_valid():
                messages.add_message(request,
                                     messages.SUCCESS,
                                     _('Form is successifully updated'))
                form.save()
                return redirect('individual-detail', ind_id=form.instance.id)

        else:
            form = CreateIndividualForm(instance=individual)

    return render_to_response("profile_individual.html", {
        "form": form,
    }, RequestContext(request))


@login_required(login_url='login/')
def survey_detail(request, survey_id=-1):
    survey = models.Survey.objects.filter(id=survey_id).first()
    if not survey:
        survey = models.Survey()
        ind_id = request.GET.get("ind_id")
        individual = models.Individual.objects.get(id=ind_id)
        if individual:
            survey.individual = individual
            survey.date = datetime.date.today()
            # TODO : improve how we get stage
            stage = models.Stage.objects.get(id=request.GET.get("stage_id"))
            if not stage:
                stage = individual.species.stage_set.\
                    filter(is_active=True).all().first()
            survey.stage = stage

    if request.POST:
        form = SurveyForm(request.POST,
                          instance=survey)

        if form.is_valid():
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
            return redirect('survey-detail', survey_id=form.instance.id)
        else:
            print form.errors
    else:
        form = SurveyForm(instance=survey)
    return render_to_response("survey.html", {
        "form": form,
    }, RequestContext(request))


@login_required(login_url='login/')
def user_detail(request):

    if request.POST:
        form = AccountForm(request.POST,
                           instance=request.user.observer)
        if form.is_valid():
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
        else:
            print form.errors
    else:
        form = AccountForm(instance=request.user.observer)

    return render_to_response("profile.html", {
        "form": form,
    }, RequestContext(request))


def register_user(request):
    if request.user:
        return redirect(index)

    if request.POST:
        form = AccountForm(request.POST)
        if form.is_valid():
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
        else:
            print form.errors
    else:
        instance = models.Observer()
        instance.user = User()
        form = AccountForm(instance=instance)

    return render_to_response("generic_form.html", {
        "form": form,
    }, RequestContext(request))


@login_required(login_url='login/')
def dashboard(request):
    return render_to_response("profile_display.html", RequestContext(request))


@login_required(login_url='login/')
def all_surveys(request):
    surveys = models.Survey.objects.all()[:100]
    return render_to_response("all_surveys.html", {
        "surveys": surveys
        }, RequestContext(request))


def get_surveys(request):
    mapping = {
        "id": "id",
        "observer": "observer",
        "date": "date",
        "species": "individual__species__name",
        "individual": "individual__name",
        "area": "individual__area__name",
        "stage": "stage__name",
        "answer": "answer"
    }
    parsed = parser.parse(request.GET.urlencode())
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search = request.GET.get("search[value]", "")
    draw = request.GET.get("draw", 1)
    query = models.Survey.objects
    query = query.filter(Q(individual__name__icontains=search)
                         | Q(individual__area__name__icontains=search)
                         | Q(individual__species__name__icontains=search)
                         | Q(individual__species__name__icontains=search))

    for ord in parsed["order"].values():
        col = parsed["columns"][ord["column"]]["data"]
        query_1 = mapping.get(col, col)
        if ord["dir"] == "desc":
            query_1 = "-" + query_1
        query = query.order_by(query_1)

    filtered_total = query.count()
    filtered_data = query.all()[start: start + length]
    response_data = {
        "draw": int(draw),
        "data": [{"id": o.id,
                  "date": str(o.date),
                  "area": o.individual.area.name,
                  "species": o.individual.species.name,
                  "individual": o.individual.name,
                  "observer": o.observer,
                  "stage": o.stage.name,
                  "answer": o.answer} for o in filtered_data],
        "recordsTotal": models.Survey.objects.count(),
        "recordsFiltered": filtered_total
    }
    return HttpResponse(json.dumps(response_data),
                        content_type="application/json")
