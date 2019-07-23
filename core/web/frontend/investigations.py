from __future__ import unicode_literals

from flask_classy import route
from flask_login import current_user
from flask import render_template, request, flash, redirect, url_for
from mongoengine import DoesNotExist, Q

from core.web.frontend.generic import GenericView
from core.investigation import Investigation, ImportMethod, ImportResults
from core.web.helpers import get_object_or_404, get_user_groups
from core.web.helpers import requires_permissions, group_user_permission

from core.database import AttachedFile
from core.entities import Entity
from core.indicators import Indicator
from core.observables import Observable

from core.web.api.api import bson_renderer


class InvestigationView(GenericView):

    klass = Investigation

    @route("/graph/<id>")
    @requires_permissions("read", "investigation")
    def graph(self, id):
        investigation = get_object_or_404(Investigation, id=id)
        if group_user_permission(investigation):
            return render_template(
                "{}/graph.html".format(self.klass.__name__.lower()),
                investigation=bson_renderer(investigation.info()))

        abort(403)

    @route("/graph/<klass>/<id>")
    @requires_permissions("read", "investigation")
    def graph_node(self, klass, id):
        if klass == 'entity':
            node = get_object_or_404(Entity, id=id)
        elif klass == 'indicator':
            node = get_object_or_404(Indicator, id=id)
        else:
            node = get_object_or_404(Observable, id=id)

        investigation = Investigation(created_by=current_user.username).save()
        investigation.add([], [node])

        return render_template(
            "{}/graph.html".format(self.klass.__name__.lower()),
            investigation=bson_renderer(investigation.info()))

    @route("/import/<id>", methods=['GET'])
    @requires_permissions("write", "investigation")
    def import_wait(self, id):
        results = get_object_or_404(ImportResults, id=id)

        return render_template(
            "{}/import_wait.html".format(self.klass.__name__.lower()),
            import_results=results)

    @route("/import", methods=['GET', 'POST'])
    @requires_permissions("write", "investigation")
    def inv_import(self):
        if request.method == "GET":
            return render_template(
                "{}/import.html".format(self.klass.__name__.lower()),
                groups=get_user_groups())
        else:
            text = request.form.get('text')
            url = request.form.get('url')
            sharing = request.form.get('sharing')

            if text:
                investigation = Investigation(
                    created_by=current_user.username, import_text=text)
                # set sharing permissions
                investigation.save()
                investigation.sharing_permissions(sharing)
                return redirect(
                    url_for(
                        'frontend.InvestigationView:import_from',
                        id=investigation.id))
            else:
                try:
                    if url:
                        import_method = ImportMethod.objects.get(acts_on="url")
                        results = import_method.run(url)
                    elif "file" in request.files:
                        target = AttachedFile.from_upload(request.files['file'])
                        import_method = ImportMethod.objects.get(
                            acts_on=target.content_type)
                        results = import_method.run(target)
                    else:
                        flash("You need to provide an input", "danger")
                        return redirect(request.referrer)
                    return redirect(
                        url_for(
                            'frontend.InvestigationView:import_wait',
                            id=results.id))
                except DoesNotExist:
                    flash("This file type is not supported.", "danger")
                    return render_template(
                        "{}/import.html".format(self.klass.__name__.lower()))

    @route("/<id>/import", methods=['GET'])
    @requires_permissions("write", "investigation")
    def import_from(self, id):
        investigation = get_object_or_404(Investigation, id=id)
        observables = Observable.from_string(investigation.import_text)

        return render_template(
            "{}/import_from.html".format(self.klass.__name__.lower()),
            investigation=investigation,
            observables=bson_renderer(observables))

    def handle_form(self, *args, **kwargs):
        kwargs['skip_validation'] = True
        return super(InvestigationView, self).handle_form(*args, **kwargs)
