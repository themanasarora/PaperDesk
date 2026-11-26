(function () {
  var form = document.querySelector("form[data-active]");
  if (!form) return;
  document.documentElement.classList.add("js");
  var panels = {};
  form.querySelectorAll("[data-panel]").forEach(function (p) { panels[p.dataset.panel] = p; });
  var items = Array.prototype.slice.call(document.querySelectorAll(".rail-item"));
  var order = ["template", "upload", "report"];

  function show(step) {
    Object.keys(panels).forEach(function (k) { panels[k].classList.toggle("is-active", k === step); });
    items.forEach(function (it) {
      var s = it.dataset.step;
      it.classList.toggle("is-active", s === step);
      it.classList.toggle("is-done", order.indexOf(s) < order.indexOf(step));
    });
  }
  items.forEach(function (it) {
    if (panels[it.dataset.step]) it.addEventListener("click", function () { show(it.dataset.step); });
  });
  form.querySelectorAll("[data-go]").forEach(function (b) {
    b.addEventListener("click", function () { show(b.dataset.go); });
  });

  var custom = form.querySelector(".custom-template");
  function syncCustom() {
    var sel = form.querySelector('input[name="ruleset"]:checked');
    if (sel && sel.value === "custom") custom.removeAttribute("data-hidden");
    else custom.setAttribute("data-hidden", "");
  }
  form.querySelectorAll('input[name="ruleset"]').forEach(function (r) { r.addEventListener("change", syncCustom); });
  syncCustom();

  var paper = form.querySelector('input[name="paper"]');
  var label = form.querySelector(".drop-text");
  paper.addEventListener("change", function () {
    label.textContent = paper.files.length ? paper.files[0].name : "Drop your .docx here, or browse";
  });
  show(form.dataset.active);
})();
