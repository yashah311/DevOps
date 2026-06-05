import jenkins.model.*
import hudson.security.*

def env = System.getenv()

def username = env.JENKINS_USER ?: "admin"
def password = env.JENKINS_PASS ?: "admin"

def instance = Jenkins.get()

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount(username, password)
instance.setSecurityRealm(hudsonRealm)

// Optional: full access to logged-in users
instance.setAuthorizationStrategy(new FullControlOnceLoggedInAuthorizationStrategy())

instance.save()
