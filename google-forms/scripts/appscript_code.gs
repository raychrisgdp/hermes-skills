/**
 * Google Forms API via Apps Script
 * Project Name: GForm Automation
 *
 * Deploy as Web App:
 *   Execute as: Me
 *   Who has access: Anyone
 *
 * SECURITY: This web-app uses a shared secret for authentication.
 * The secret is passed in each request as payload["secret"].
 * Set SHARED_SECRET to a random value before deploying.
 */

var SHARED_SECRET = ""; // Set this to a random secret string before deploying

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);

    // Auth check — skip when secret is empty (backwards compatible for testing).
    // Once SHARED_SECRET is set, all requests must include "secret".
    if (SHARED_SECRET) {
      var reqSecret = payload.secret || "";
      if (reqSecret !== SHARED_SECRET) {
        return respond({ error: 'Unauthorized: invalid or missing secret' });
      }
    }

    var action = payload.action;
    if (!action) return respond({ error: 'Missing "action" field' });

    switch (action) {
      case 'create':       return createForm(payload);
      case 'get':          return getForm(payload);
      case 'list':         return listForms();
      case 'addQuestions': return addQuestions(payload);
      case 'responses':    return getResponses(payload);
      default:             return respond({ error: 'Unknown action: ' + action });
    }
  } catch (err) {
    return respond({ error: err.toString() });
  }
}

function createForm(p) {
  var form = FormApp.create(p.title);
  if (p.description) form.setDescription(p.description);
  if (Array.isArray(p.questions)) p.questions.forEach(function(q) { addQuestion(form, q); });
  return respond({ status: 'created', title: form.getTitle(), formId: form.getId(), editUri: form.getEditUrl(), responderUri: form.getPublishedUrl() });
}

function getForm(p) {
  var form = FormApp.openById(p.formId);
  var items = form.getItems().map(function(it, i) { return { index: i, type: String(it.getType()), title: it.getTitle() }; });
  return respond({ title: form.getTitle(), description: form.getDescription(), responderUri: form.getPublishedUrl(), questionCount: items.length, questions: items });
}

function listForms() {
  var files = DriveApp.getFilesByType(MimeType.GOOGLE_FORMS);
  var out = [];
  while (files.hasNext()) {
    var f = files.next();
    out.push({ id: f.getId(), name: f.getName(), url: f.getUrl(), modified: f.getLastUpdated() });
  }
  return respond({ count: out.length, forms: out });
}

function addQuestions(p) {
  var form = FormApp.openById(p.formId);
  var n = 0;
  (p.questions || []).forEach(function(q) { addQuestion(form, q); n++; });
  return respond({ status: 'added', count: n, formId: p.formId });
}

function getResponses(p) {
  var form = FormApp.openById(p.formId);
  return respond({
    formId: p.formId,
    count: form.getResponses().length,
    responses: form.getResponses().map(function(r) {
      return {
        id: r.getId(),
        timestamp: r.getTimestamp(),
        answers: r.getItemResponses().map(function(a) {
          return { question: a.getItem().getTitle(), answer: a.getResponse() };
        })
      };
    })
  });
}

function addQuestion(form, q) {
  var r = q.required === true;
  var item;

  switch (q.type) {
    case 'text':
      item = form.addTextItem().setTitle(q.title).setRequired(r);
      break;
    case 'paragraph':
      item = form.addParagraphTextItem().setTitle(q.title).setRequired(r);
      break;
    case 'multiple_choice':
      item = form.addMultipleChoiceItem().setTitle(q.title).setRequired(r);
      var mcOpts = (q.options || []).map(function(o) { return item.createChoice(o); });
      item.setChoices(mcOpts);
      break;
    case 'checkbox':
      item = form.addCheckboxItem().setTitle(q.title).setRequired(r);
      var cbOpts = (q.options || []).map(function(o) { return item.createChoice(o); });
      item.setChoices(cbOpts);
      break;
    case 'dropdown':
      item = form.addListItem().setTitle(q.title).setRequired(r);
      var ddOpts = (q.options || []).map(function(o) { return item.createChoice(o); });
      item.setChoices(ddOpts);
      break;
    case 'scale':
      // Google Apps Script addScaleItem() doesn't support setLowerBound/setUpperBound.
      // Use multiple_choice with numbered options as a workaround.
      var min = q.scaleMin || 1;
      var max = q.scaleMax || 5;
      item = form.addMultipleChoiceItem().setTitle(q.title).setRequired(r);
      var scaleOpts = [];
      for (var i = min; i <= max; i++) {
        scaleOpts.push(item.createChoice(String(i)));
      }
      item.setChoices(scaleOpts);
      break;
    case 'date':
      item = form.addDateItem().setTitle(q.title).setRequired(r);
      break;
    case 'time':
      item = form.addTimeItem().setTitle(q.title).setRequired(r);
      break;
    case 'datetime':
      item = form.addDateTimeItem().setTitle(q.title).setRequired(r);
      break;
    case 'duration':
      item = form.addDurationItem().setTitle(q.title).setRequired(r);
      break;
    case 'email':
      item = form.addTextItem().setTitle(q.title).setRequired(r);
      item.setValidation(FormApp.createTextValidation().requireTextIsEmail().build());
      break;
    case 'grid':
      item = form.addGridItem().setTitle(q.title).setRequired(r);
      item.setRows(q.rows || []);
      item.setColumns(q.cols || []);
      break;
    default:
      throw new Error('Unknown question type: ' + q.type);
  }
  return item;
}

function respond(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}
