# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""Tests for task group task specific export."""
import unittest
from collections import defaultdict

from ddt import data, unpack, ddt

from integration.ggrc_workflows.models import factories
from integration.ggrc import TestCase
from integration.ggrc.models import factories as ggrc_factories

from ggrc.models import all_models


@unittest.skip("Skip cause of feature cut.")
@ddt
class TestExportTasks(TestCase):
  """Test imports for basic workflow objects."""

  def setUp(self):
    super(TestExportTasks, self).setUp()
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "GGRC",
        "X-export-view": "blocks",
    }

  @staticmethod
  def generate_tasks_for_cycle(cycle_count, task_count):
    """generate seceted number of cycles and tasks"""
    role_names = ("Task Assignees", "Task Secondary Assignees")
    results = {}
    with ggrc_factories.single_commit():
      for _ in range(cycle_count):
        workflow = factories.WorkflowFactory()
        cycle = factories.CycleFactory(
            workflow=workflow,
        )
        cycle.contact = ggrc_factories.PersonFactory(
            name="user for cycle {}".format(cycle.id)
        )
        person = ggrc_factories.PersonFactory(
            name="user for cycle tasks {}".format(cycle.id)
        )
        task_group = factories.TaskGroupFactory(workflow=workflow)
        for _ in range(task_count):
          task_group_task = factories.TaskGroupTaskFactory(
              task_group=task_group)
          for r_name in role_names:
            role = all_models.AccessControlRole.query.filter(
                all_models.AccessControlRole.name == r_name,
                all_models.AccessControlRole.object_type ==
                task_group_task.type,
            ).one()
            ggrc_factories.AccessControlListFactory(ac_role=role,
                                                    object=task_group_task,
                                                    person=person)
          cycle_task_group = factories.CycleTaskGroupFactory(
              cycle=cycle, contact=person)

          task = factories.CycleTaskFactory(cycle=cycle,
                                            cycle_task_group=cycle_task_group,
                                            task_group_task=task_group_task)
          for r_name in role_names:
            role = all_models.AccessControlRole.query.filter(
                all_models.AccessControlRole.name == r_name,
                all_models.AccessControlRole.object_type == task.type,
            ).one()
            ggrc_factories.AccessControlListFactory(ac_role=role,
                                                    object=task,
                                                    person=person)
          results[task.id] = cycle.slug
    return results

  # pylint: disable=invalid-name
  def assertCycles(self, field, value, cycle_slugs):
    """assertion for search cycles for selected fields and values"""
    search_request = [{
        "object_name": "Cycle",
        "filters": {
            "expression": {
                "left": field,
                "op": {"name": "="},
                "right": value,
            },
        },
        "fields": ["slug"],
    }]
    parsed_data = self.export_parsed_csv(search_request)["Cycle"]
    self.assertEqual(sorted(cycle_slugs),
                     sorted([i["Code*"] for i in parsed_data]))
    self.assertEqual(len(cycle_slugs), len(parsed_data))

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_task_title(self, cycle_count, task_count):
    """Test filter cycles by task slug and title"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      self.assertCycles("task title", task.title, [slug])

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_group_title(self, cycle_count, task_count):
    """Test filter cycles by group slug and title"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      self.assertCycles("group title", task.cycle_task_group.title, [slug])

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_task_due_date(self, cycle_count, task_count):
    """Test filter cycles by task due date"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    due_date_dict = defaultdict(set)
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      due_date_dict[str(task.end_date)].add(slug)

    for due_date, cycle_slugs in due_date_dict.iteritems():
      self.assertCycles("task due date", due_date, list(cycle_slugs))

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_group_due_date(self, cycle_count, task_count):
    """Test filter cycles by group due date"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    due_date_dict = defaultdict(set)
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      due_date_dict[str(task.cycle_task_group.next_due_date)].add(slug)

    for due_date, cycle_slugs in due_date_dict.iteritems():
      self.assertCycles("group due date", due_date, list(cycle_slugs))

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_group_assignee(self, cycle_count, task_count):
    """Test filter cycles by group assignee name or email"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      self.assertCycles(
          "group assignee", task.cycle_task_group.contact.email, [slug])
      self.assertCycles(
          "group assignee", task.cycle_task_group.contact.name, [slug])

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_task_assignee(self, cycle_count, task_count):
    """Test filter cycles by task assignee name or email"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      assignees = list(self.get_persons_for_role_name(
          task, "Task Assignees"))
      self.assertEqual(1, len(assignees))
      self.assertCycles("task assignees", assignees[0].email, [slug])
      self.assertCycles("task assignees", assignees[0].name, [slug])

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_task_secondary_assignee(self, cycle_count, task_count):
    """Test filter cycles by task secondary assignee name or email"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      s_assignees = list(self.get_persons_for_role_name(
          task, "Task Secondary Assignees"))
      self.assertEqual(1, len(s_assignees))
      self.assertCycles("task secondary assignees",
                        s_assignees[0].email, [slug])
      self.assertCycles("task secondary assignees",
                        s_assignees[0].name, [slug])

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_task_due_date_year(self, cycle_count, task_count):
    """Test filter cycles by task due date year"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    due_date_dict = defaultdict(set)
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      key = (task.end_date.year, task.end_date.month, task.end_date.day)
      due_date_dict[key].add(slug)

    for due_date, cycle_slugs in due_date_dict.iteritems():
      self.assertCycles("task due date",
                        "{}-{}-{}".format(*due_date),
                        list(cycle_slugs))

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_task_due_date_year_month(self, cycle_count, task_count):
    """Test filter cycles by task due date year month"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    due_date_dict = defaultdict(set)
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      due_date_dict[(task.end_date.year, task.end_date.month)].add(slug)

    for due_date, cycle_slugs in due_date_dict.iteritems():
      self.assertCycles("task due date",
                        "{}-{}".format(*due_date),
                        list(cycle_slugs))

  @data(
      #  (Cycle count, tasks in cycle)
      (0, 0),
      (1, 1),
      (2, 1),
      (2, 1),
      (2, 2),
  )
  @unpack
  def test_filter_by_cycle_assignee(self, cycle_count, task_count):
    """Test filter cycles by cycle assignee name and email"""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    self.assertEqual(bool(cycle_count), bool(task_cycle_filter))
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      self.assertCycles("cycle assignee", task.cycle.contact.email, [slug])
      self.assertCycles("cycle assignee", task.cycle.contact.name, [slug])

  @data(
      #  (Cycle count, tasks in cycle)
      (2, 2),
  )
  @unpack
  def test_filter_by_task_comment(self, cycle_count, task_count):
    """Test filter cycles by task comments."""
    task_cycle_filter = self.generate_tasks_for_cycle(cycle_count, task_count)
    filter_params = {}
    for task_id, slug in task_cycle_filter.iteritems():
      task = all_models.CycleTaskGroupObjectTask.query.filter(
          all_models.CycleTaskGroupObjectTask.id == task_id
      ).one()
      comment = "comment for task # {}".format(task_id)
      factories.CycleTaskEntryFactory(
          cycle_task_group_object_task=task,
          description=comment,
      )
      filter_params[comment] = slug

    for comment, slug in filter_params.iteritems():
      self.assertCycles("task comments", comment, [slug])
