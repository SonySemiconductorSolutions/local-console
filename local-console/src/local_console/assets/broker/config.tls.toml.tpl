listener ${mqtt_port}
connection_messages true
log_timestamp false

allow_anonymous false
require_certificate true
use_identity_as_username true

cafile ${ca_crt}
certfile ${server_crt}
keyfile ${server_key}
