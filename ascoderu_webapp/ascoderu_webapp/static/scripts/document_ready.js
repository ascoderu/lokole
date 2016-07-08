$(function updateActiveNavLink() {
  $('nav a[href^="/' + location.pathname.split("/")[1] + '"]')
    .closest("li")
    .addClass('active');
});
