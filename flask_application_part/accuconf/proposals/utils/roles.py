from enum import Enum


class Role(Enum):
    admin = 'admin'
    reviewer = 'reviewer'
    user = 'user'


role_descriptions = {
    Role.admin: 'Super user.',
    Role.reviewer: 'A person that reviews, scores, and comments on proposals.',
    Role.user: 'A submitter of proposals.',
}
