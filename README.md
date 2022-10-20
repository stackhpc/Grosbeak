## Canary 
### A quick CI health check for your OpenStack cloud.
All configuration happens in `config.yml`.

Defaults can be left as they are.

OS cloud variables can either be configured in config.yml, or left blank if OS cloud variables are set in the environment (such as by an RC file from Horizon).

`pub_net_id` is the network on which VMs will be spun up.

`floating_ips` should be set to True if `pub_net_id` is not directly reachable by the machine running this test.

`floating_net_id` should be set if `floating_ips` is True.

config for the health monitor will look something like: 

```
floating_ips: True
floating_net_id: c75dd66e-7e1a-4b33-9240-9bc4ce452331
pub_net_id: f3870bba-16f1-43b3-8bb1-3c41659f2ee0
images:
  - b80cfa15-482f-4bc8-9cca-1493c9b4eccc
  - d2ac6a57-3669-44aa-a9f3-9690647ad1c5
ssh_users:
  - ubuntu
  - cirros
flavors:
  - 1
  - 2
```

where `ssh_users` correspond to the images provided. It doesn't matter what order you put flavor/image/ssh_user, however the ssh_user that will be used for each image needs to be in the same order as the images (i.e. user `ubuntu` will be used for the image `b80c...`, `cirros` will be used for image `d2ac...` etc). HealthMonitor will run through all combinations of flavors and images. Additionally, you can set flavors_alt, images_alt and ssh_users_alt for a second group of compatible images/flavors that will also be run.