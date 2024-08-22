# Push_to_Sync Architecture

### CURRENT SITUATION
* DevOps team manually deploys their scripts/folders on all linux servers.

### SOLUTION
* The required data can be committed, pushed on to GitHub (Frontend URL/Backend server) by the DevOps TA user and a custom webhook will trigger the jenkins job that calls the ansible playbook to perform synchronized deployments on all the specified linux servers.

### BENEFITS
* No dependency on third party applications like WinSCP or data transfer tools that TA team needs to do manually. Any authentic GitHub user can directly(on a single commit) push & synchronize the scripts/folders on all linux servers. Also, the version can be controlled, commit history can be tracked from the GitHub repository itself.
