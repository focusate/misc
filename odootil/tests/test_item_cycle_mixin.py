from psycopg2 import IntegrityError

from odoo.tools.misc import mute_logger

from .. models.odootil_item_cycle import (
    ITEM_CYCLE_START_FIELD,
    ITEM_CYCLE_END_FIELD,
    ITEM_CYCLE_CONTAINER_FIELD
)
from .common import TestOdootilCommon, SQL_DB_PATH


class TestItemCycleMixin(TestOdootilCommon):
    """Test class for odootil.item_cycle mixin."""

    @classmethod
    def _create_cycle_test_week(cls, position):
        return cls.ItemCycleTestWeek.create({'position': position})

    @classmethod
    def _create_cycle_test_weeks(cls):
        def _setattr(pos, item):
            setattr(cls, 'week_%s' % pos, item)
        # Create items not in order, to make sure they are ordered, when
        # computing.
        for pos in range(3, 5):
            item = cls._create_cycle_test_week(pos)
            _setattr(pos, item)
        for pos in range(1, 3):
            item = cls._create_cycle_test_week(pos)
            _setattr(pos, item)

    @classmethod
    def setUpClass(cls):
        """Set up common data for mixin tests."""
        super().setUpClass()
        cls.ItemCycleTestWeek = cls.env['item_cycle.test.week']
        cls.ItemCycleTestWeekContainer = cls.env[
            'item_cycle.test.week.container']
        cls._create_cycle_test_weeks()
        cls.container_1 = cls.ItemCycleTestWeekContainer.create({
            'name': 'container 1',
            ITEM_CYCLE_START_FIELD: cls.week_1.id,
            ITEM_CYCLE_END_FIELD: cls.week_3.id,
        })
        cls.container_2 = cls.ItemCycleTestWeekContainer.create({
            'name': 'container 1',
            ITEM_CYCLE_START_FIELD: cls.week_4.id,
            ITEM_CYCLE_END_FIELD: cls.week_2.id,
        })

    @mute_logger(SQL_DB_PATH)
    def test_01_check_cycle_test_week_unique(self):
        """Try to create non unique week item."""
        with self.assertRaises(IntegrityError):
            self._create_cycle_test_week(2)

    def test_02_check_cycle_test_week_ondelete(self):
        """Delete non start/end week."""
        self.container_1[ITEM_CYCLE_END_FIELD] = self.week_4.id
        try:
            self.week_3.unlink()
            self.assertEqual(
                sorted(self.container_1[ITEM_CYCLE_CONTAINER_FIELD].ids),
                sorted((self.week_1 | self.week_2 | self.week_4).ids)
            )
        except IntegrityError:
            self.fail("Non star/end week should be deleted.")

    @mute_logger(SQL_DB_PATH)
    def test_03_check_cycle_test_week_ondelete(self):
        """Try to delete week, which is start week on container."""
        with self.assertRaises(IntegrityError):
            self.week_1.unlink()

    @mute_logger(SQL_DB_PATH)
    def test_04_check_cycle_test_week_ondelete(self):
        """Try to delete week, which is end week on container."""
        with self.assertRaises(IntegrityError):
            self.week_3.unlink()

    @mute_logger(SQL_DB_PATH)
    def test_05_check_cycle_test_week_container_create(self):
        """Try to create container with only start week."""
        with self.assertRaises(IntegrityError):
            self.ItemCycleTestWeekContainer.create({
                        'name': 'container 3',
                        ITEM_CYCLE_START_FIELD: self.week_1.id,
                    })

    @mute_logger(SQL_DB_PATH)
    def test_06_check_cycle_test_week_container_create(self):
        """Try to create container with only end week."""
        with self.assertRaises(IntegrityError):
            self.ItemCycleTestWeekContainer.create({
                        'name': 'container 3',
                        ITEM_CYCLE_END_FIELD: self.week_1.id,
                    })

    def test_07_check_cycle_test_week_container_unset(self):
        """Unset Both start/end weeks."""
        try:
            self.container_1.write({
                ITEM_CYCLE_START_FIELD: False,
                ITEM_CYCLE_END_FIELD: False,
            })
        except IntegrityError:
            self.fail("Must allow unsetting both start/end at the same time.")

    @mute_logger(SQL_DB_PATH)
    def test_08_check_cycle_test_week_container_unset(self):
        """Try to unset only start week."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.container_1[ITEM_CYCLE_START_FIELD] = False

    @mute_logger(SQL_DB_PATH)
    def test_09_check_cycle_test_week_container_unset(self):
        """Try to unset only end week."""
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.container_1[ITEM_CYCLE_END_FIELD] = False

    def test_10_search_cycle_test_week(self):
        """Search for container with week 3 in range."""
        # Case 1.
        container = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', self.week_3.id)]
        )
        self.assertEqual(container, self.container_1)

    def test_11_search_cycle_test_week(self):
        """Search for container with week 4 in range."""
        # Case 1.
        container = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', self.week_4.id)]
        )
        self.assertEqual(container, self.container_2)

    def test_12_search_cycle_test_week(self):
        """Search for containers with week 1 in range."""
        # Case 1.
        containers = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', self.week_1.id)]
        )
        self.assertEqual(
            sorted(containers.ids),
            sorted((self.container_1 | self.container_2).ids)
        )

    def test_13_search_cycle_test_week(self):
        """Search for containers with week 5 in range (newly added)."""
        week_5 = self._create_cycle_test_week(5)
        container = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', week_5.id)]
        )
        self.assertEqual(container, self.container_2)

    def test_14_search_cycle_test_week(self):
        """Make week 2, week 10."""
        self.week_2.position = 10
        week_10 = self.week_2
        weeks = self.container_1[ITEM_CYCLE_CONTAINER_FIELD]
        self.assertEqual(
            sorted(weeks.ids),
            sorted((self.week_1 | self.week_3).ids),
        )
        weeks = self.container_2[ITEM_CYCLE_CONTAINER_FIELD]
        self.assertEqual(
            sorted(weeks.ids),
            sorted((self.week_4 | week_10).ids),
        )

    def test_15_search_cycle_test_week(self):
        """Change container to no longer include week 4."""
        self.container_2[ITEM_CYCLE_START_FIELD] = self.week_1
        container = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', self.week_4.id)]
        )
        self.assertFalse(container)

    def test_16_search_cycle_test_week(self):
        """Change container to have same start/end."""
        # Removing container 2, to not be included in search.
        self.container_2.unlink()
        self.container_1[ITEM_CYCLE_END_FIELD] = self.week_1
        container = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', self.week_1.id)]
        )
        self.assertEqual(container, self.container_1)
        container = self.ItemCycleTestWeekContainer.search(
            [(ITEM_CYCLE_CONTAINER_FIELD, 'in', self.week_2.id)]
        )
        self.assertFalse(container)

    def test_17_search_cycle_test_week(self):
        """Search with container field using name_search.

        Case 1: numeric string.
        Case 2: non numeric string.
        Case 3: alphanumeric string.
        """
        # Case 1.
        week_1_id = self.week_1.id
        res = self.ItemCycleTestWeek.name_search('1', operator='=')
        self.assertEqual(res[0][0], week_1_id)
        # Case 2.
        res = self.ItemCycleTestWeek.name_search('abcdf', operator='=')
        self.assertFalse(res)
        # Case 3.
        res = self.ItemCycleTestWeek.name_search('w1bcs', operator='=')
        self.assertEqual(res[0][0], week_1_id)
