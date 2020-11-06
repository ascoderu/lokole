provider "cloudflare" {
  email = var.cloudflare_user
  token = var.cloudflare_key
}

resource "cloudflare_record" "www" {
  domain  = "${var.ingressip}"
  name    = "${var.lokole_dns_name}"
  value   = "203.0.113.10"
  type    = "A"
  proxied = false
}